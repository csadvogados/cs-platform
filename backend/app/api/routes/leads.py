from datetime import datetime, timedelta, timezone
from html import escape
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy import Integer, func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.deps import require_permissions
from app.db.session import get_db
from app.models.client import Client
from app.models.crm import CommercialContract, ContractTemplate, Lead, LeadInteraction, LeadProposal, LeadSource, LeadTask, ServiceType
from app.models.organization import Organization
from app.models.recovery import RecoveryCaseSource
from app.models.user import User
from app.schemas.leads import *
from app.schemas.recovery import RecoveryCaseCreate
from app.security.identity import IdentityContext
from app.security.permissions import PermissionCode
from app.services.audit import record_audit
from app.services.recovery_cases import create_case

router = APIRouter()
DEFAULT_SOURCES = [("INDICACAO","Indicação"),("INSTAGRAM","Instagram"),("FACEBOOK","Facebook"),("GOOGLE","Google"),("WHATSAPP","WhatsApp"),("SITE","Site"),("CLIENTE_ANTIGO","Cliente antigo"),("PARCEIRO","Parceiro"),("EVENTO","Evento"),("PROSPECCAO_PERMITIDA","Prospecção permitida"),("OUTRO","Outro")]
DEFAULT_SERVICES = [("CS_RECUPERA","CS Recupera"),("CONSUMIDOR","Consumidor"),("BANCARIO","Bancário"),("PREVIDENCIARIO","Previdenciário"),("FAMILIA","Família"),("INVENTARIO","Inventário / Sucessões"),("TRABALHISTA","Trabalhista"),("CRIMINAL","Criminal"),("ENERGIA","Energia"),("CONSULTORIA","Consultoria"),("CS_CAPTA_RECURSOS","CS Capta Recursos"),("OUTRO","Outro")]


def get_lead(db: Session, ident: IdentityContext, lead_id: UUID) -> Lead:
    obj = db.scalar(select(Lead).where(Lead.id == lead_id, Lead.organization_id == ident.organization_id, Lead.deleted_at.is_(None)))
    if not obj: raise HTTPException(404, "Lead não encontrado")
    return obj


def validate_fk(db, ident, model, value, label):
    if value is None: return
    if not db.scalar(select(model.id).where(model.id == value, model.organization_id == ident.organization_id)):
        raise HTTPException(422, f"{label} não pertence à organização")


def save(db):
    try: db.commit()
    except IntegrityError as exc:
        db.rollback(); raise HTTPException(409, "Conflito ao salvar lead") from exc


def default_contract_content(organization, client, lead, proposal):
    office = organization.trade_name or organization.legal_name
    service = "serviços jurídicos contratados"
    return (
        f"CONTRATO DE PRESTAÇÃO DE SERVIÇOS ADVOCATÍCIOS\n\n"
        f"CONTRATADA: {office}.\n"
        f"CONTRATANTE: {client.full_name}, CPF {client.cpf}.\n\n"
        f"OBJETO: prestação de {service}, conforme a proposta comercial vinculada.\n\n"
        f"HONORÁRIOS: valor fixo de R$ {float(proposal.fixed_value):,.2f}; entrada de R$ {float(proposal.down_payment):,.2f}; "
        f"{proposal.installments} parcela(s) de R$ {float(proposal.installment_value):,.2f}; êxito de {float(proposal.success_percentage):g}%.\n\n"
        "As condições específicas, obrigações das partes, vigência e hipóteses de rescisão deverão ser revisadas antes da aprovação.\n\n"
        "Ao aprovar este documento, a equipe confirma que o conteúdo foi revisado. O registro de assinatura nesta plataforma é manual."
    )


def render_contract_template(content, organization, client, service, proposal):
    values = {
        "escritorio": organization.trade_name or organization.legal_name,
        "cliente_nome": client.full_name,
        "cliente_cpf": client.cpf or "não informado",
        "servico": service.name if service else "serviços jurídicos contratados",
        "valor_fixo": f"R$ {float(proposal.fixed_value):,.2f}",
        "entrada": f"R$ {float(proposal.down_payment):,.2f}",
        "parcelas": str(proposal.installments),
        "valor_parcela": f"R$ {float(proposal.installment_value):,.2f}",
        "percentual_exito": f"{float(proposal.success_percentage):g}",
    }
    rendered = content
    for key, value in values.items():
        rendered = rendered.replace("{{" + key + "}}", value)
    return rendered


def ensure_catalogs(db: Session, organization_id: UUID):
    if not db.scalar(select(LeadSource.id).where(LeadSource.organization_id == organization_id).limit(1)):
        db.add_all([LeadSource(organization_id=organization_id, code=code, name=name) for code, name in DEFAULT_SOURCES])
    if not db.scalar(select(ServiceType.id).where(ServiceType.organization_id == organization_id).limit(1)):
        db.add_all([ServiceType(organization_id=organization_id, code=code, name=name) for code, name in DEFAULT_SERVICES])
    db.flush()


@router.get("/catalogs")
def catalogs(db: Session = Depends(get_db), ident: IdentityContext = Depends(require_permissions(PermissionCode.CRM_READ.value))):
    org = ident.organization_id
    ensure_catalogs(db, org); db.commit()
    return {
        "sources": list(db.scalars(select(LeadSource).where(LeadSource.organization_id == org, LeadSource.active.is_(True)).order_by(LeadSource.name))),
        "services": list(db.scalars(select(ServiceType).where(ServiceType.organization_id == org, ServiceType.active.is_(True)).order_by(ServiceType.name))),
    }


@router.get("", response_model=list[LeadRead])
def list_leads(search: str | None = None, lead_status: LeadStatus | None = Query(None, alias="status"), source_id: UUID | None = None,
               service_type_id: UUID | None = None, owner_id: UUID | None = None, priority: LeadPriority | None = None,
               date_from: datetime | None = None, date_to: datetime | None = None, overdue_only: bool = False,
               limit: int = Query(100, ge=1, le=200), offset: int = Query(0, ge=0),
               db: Session = Depends(get_db), ident: IdentityContext = Depends(require_permissions(PermissionCode.CRM_READ.value))):
    filters = [Lead.organization_id == ident.organization_id, Lead.deleted_at.is_(None)]
    if search:
        term = f"%{search.strip()}%"; filters.append(or_(Lead.full_name.ilike(term), Lead.cpf.ilike(term), Lead.phone.ilike(term), Lead.whatsapp.ilike(term), Lead.email.ilike(term)))
    if lead_status: filters.append(Lead.status == lead_status)
    if source_id: filters.append(Lead.source_id == source_id)
    if service_type_id: filters.append(Lead.service_type_id == service_type_id)
    if owner_id: filters.append(Lead.owner_id == owner_id)
    if priority: filters.append(Lead.priority == priority)
    if date_from: filters.append(Lead.created_at >= date_from)
    if date_to: filters.append(Lead.created_at <= date_to)
    query = select(Lead).where(*filters)
    if overdue_only:
        query = query.join(LeadTask, LeadTask.lead_id == Lead.id).where(LeadTask.status == "PENDENTE", LeadTask.due_at < datetime.now(timezone.utc)).distinct()
    return list(db.scalars(query.order_by(Lead.updated_at.desc()).offset(offset).limit(limit)))


@router.post("", response_model=LeadRead, status_code=201)
def create_lead(payload: LeadCreate, db: Session = Depends(get_db), ident: IdentityContext = Depends(require_permissions(PermissionCode.CRM_CREATE.value))):
    validate_fk(db, ident, LeadSource, payload.source_id, "Origem"); validate_fk(db, ident, ServiceType, payload.service_type_id, "Serviço"); validate_fk(db, ident, User, payload.owner_id, "Responsável")
    obj = Lead(organization_id=ident.organization_id, **payload.model_dump())
    db.add(obj); db.flush()
    db.add(LeadInteraction(organization_id=ident.organization_id, lead_id=obj.id, user_id=ident.user_id, interaction_type="STATUS", description="Lead criado com status NOVO", occurred_at=datetime.now(timezone.utc)))
    record_audit(db, organization_id=ident.organization_id, user_id=ident.user_id, entity_type="lead", entity_id=obj.id, action="create", new_values={"name": obj.full_name, "status": obj.status})
    save(db); db.refresh(obj); return obj


@router.post("/distribution", response_model=LeadDistributionRead)
def distribute_unassigned_leads(payload: LeadDistributionCreate, db: Session = Depends(get_db), ident: IdentityContext = Depends(require_permissions(PermissionCode.CRM_UPDATE.value))):
    if not ident.is_superuser and str(ident.role).lower() not in {"admin", "supervisor"}:
        raise HTTPException(403, "Somente administradores e supervisores podem distribuir leads")
    requested_ids = list(dict.fromkeys(payload.user_ids))
    users = list(db.scalars(select(User).where(
        User.id.in_(requested_ids), User.organization_id == ident.organization_id,
        User.deleted_at.is_(None), User.status == "active",
    )))
    if len(users) != len(requested_ids):
        raise HTTPException(422, "Selecione apenas responsáveis ativos desta organização")
    open_statuses = {"NOVO", "CONTATADO", "QUALIFICADO", "PROPOSTA"}
    workloads = dict(db.execute(select(Lead.owner_id, func.count(Lead.id)).where(
        Lead.organization_id == ident.organization_id, Lead.deleted_at.is_(None),
        Lead.status.in_(open_statuses), Lead.owner_id.in_(requested_ids),
    ).group_by(Lead.owner_id)).all())
    users.sort(key=lambda user: (workloads.get(user.id, 0), user.full_name.casefold(), str(user.id)))
    leads = list(db.scalars(select(Lead).where(
        Lead.organization_id == ident.organization_id, Lead.deleted_at.is_(None),
        Lead.status.in_(open_statuses), Lead.owner_id.is_(None),
    ).order_by(Lead.created_at, Lead.id)))
    assigned_by_user = {user.id: 0 for user in users}
    for index, lead in enumerate(leads):
        owner = users[index % len(users)]
        lead.owner_id = owner.id
        assigned_by_user[owner.id] += 1
        db.add(LeadInteraction(
            organization_id=ident.organization_id, lead_id=lead.id, user_id=ident.user_id,
            interaction_type="STATUS", description=f"Lead distribuído para {owner.full_name}",
            occurred_at=datetime.now(timezone.utc),
        ))
        record_audit(
            db, organization_id=ident.organization_id, user_id=ident.user_id,
            entity_type="lead", entity_id=lead.id, action="assign",
            new_values={"owner_id": str(owner.id), "owner_name": owner.full_name, "method": "round_robin"},
        )
    save(db)
    remaining = db.scalar(select(func.count(Lead.id)).where(
        Lead.organization_id == ident.organization_id, Lead.deleted_at.is_(None),
        Lead.status.in_(open_statuses), Lead.owner_id.is_(None),
    )) or 0
    return LeadDistributionRead(
        assigned=len(leads), remaining_unassigned=remaining,
        owners=[LeadDistributionOwnerRead(user_id=user.id, user_name=user.full_name, assigned=assigned_by_user[user.id]) for user in users],
    )


@router.get("/analytics/team", response_model=list[LeadTeamPerformanceRead])
def team_performance(db: Session = Depends(get_db), ident: IdentityContext = Depends(require_permissions(PermissionCode.CRM_READ.value))):
    org = ident.organization_id
    now = datetime.now(timezone.utc)
    open_statuses = {"NOVO", "CONTATADO", "QUALIFICADO", "PROPOSTA"}
    users = list(db.scalars(select(User).where(
        User.organization_id == org, User.deleted_at.is_(None), User.status == "active",
    ).order_by(User.full_name, User.id)))
    result = []
    for user in users:
        base = [Lead.organization_id == org, Lead.deleted_at.is_(None), Lead.owner_id == user.id]
        assigned = db.scalar(select(func.count(Lead.id)).where(*base)) or 0
        active = db.scalar(select(func.count(Lead.id)).where(*base, Lead.status.in_(open_statuses))) or 0
        converted = db.scalar(select(func.count(Lead.id)).where(*base, Lead.status == "CONVERTIDO")) or 0
        lost = db.scalar(select(func.count(Lead.id)).where(*base, Lead.status == "PERDIDO")) or 0
        overdue = db.scalar(select(func.count(LeadTask.id)).join(Lead, Lead.id == LeadTask.lead_id).where(
            *base, LeadTask.status == "PENDENTE", LeadTask.due_at < now,
        )) or 0
        future_task = select(LeadTask.id).where(
            LeadTask.lead_id == Lead.id, LeadTask.status == "PENDENTE", LeadTask.due_at >= now,
        ).exists()
        without_action = db.scalar(select(func.count(Lead.id)).where(
            *base, Lead.status.in_(open_statuses), ~future_task,
        )) or 0
        result.append(LeadTeamPerformanceRead(
            user_id=user.id, user_name=user.full_name, assigned_leads=assigned, active_leads=active,
            converted=converted, lost=lost, overdue_tasks=overdue,
            leads_without_next_action=without_action,
            conversion_rate=round(converted * 100 / assigned, 2) if assigned else 0,
        ))
    return result


@router.get("/{lead_id}/duplicates")
def duplicate_clients(lead_id: UUID, db: Session = Depends(get_db), ident: IdentityContext = Depends(require_permissions(PermissionCode.CRM_READ.value))):
    lead = get_lead(db, ident, lead_id)
    conditions = []
    if lead.cpf: conditions.append(Client.cpf == lead.cpf)
    if lead.phone: conditions.append(Client.phone == lead.phone)
    if lead.whatsapp: conditions.append(Client.phone == lead.whatsapp)
    if lead.email: conditions.append(func.lower(Client.email) == lead.email.lower())
    if not conditions: return []
    matches = db.scalars(select(Client).where(Client.organization_id == ident.organization_id, Client.archived_at.is_(None), or_(*conditions))).all()
    return [{"id": item.id, "full_name": item.full_name, "cpf": item.cpf, "phone": item.phone, "email": item.email} for item in matches]


@router.get("/{lead_id}", response_model=LeadRead)
def read_lead(lead_id: UUID, db: Session = Depends(get_db), ident: IdentityContext = Depends(require_permissions(PermissionCode.CRM_READ.value))): return get_lead(db, ident, lead_id)


@router.patch("/{lead_id}", response_model=LeadRead)
def update_lead(lead_id: UUID, payload: LeadUpdate, db: Session = Depends(get_db), ident: IdentityContext = Depends(require_permissions(PermissionCode.CRM_UPDATE.value))):
    obj = get_lead(db, ident, lead_id); changes = payload.model_dump(exclude_unset=True)
    for field, model, label in (("source_id", LeadSource, "Origem"), ("service_type_id", ServiceType, "Serviço"), ("owner_id", User, "Responsável")):
        if field in changes: validate_fk(db, ident, model, changes[field], label)
    before = {key: str(getattr(obj, key)) for key in changes}
    for key, value in changes.items(): setattr(obj, key, value)
    record_audit(db, organization_id=ident.organization_id, user_id=ident.user_id, entity_type="lead", entity_id=obj.id, action="update", new_values={"before": before, "after": {k: str(v) for k, v in changes.items()}})
    save(db); db.refresh(obj); return obj


@router.post("/{lead_id}/status", response_model=LeadRead)
def change_status(lead_id: UUID, payload: StatusChange, db: Session = Depends(get_db), ident: IdentityContext = Depends(require_permissions(PermissionCode.CRM_UPDATE.value))):
    obj = get_lead(db, ident, lead_id)
    if payload.status == "CONVERTIDO": raise HTTPException(422, "Use o endpoint de conversão")
    old = obj.status; obj.status = payload.status
    obj.lost_reason = payload.lost_reason if payload.status == "PERDIDO" else None; obj.lost_notes = payload.lost_notes if payload.status == "PERDIDO" else None
    db.add(LeadInteraction(organization_id=ident.organization_id, lead_id=obj.id, user_id=ident.user_id, interaction_type="STATUS", description=f"Status alterado de {old} para {obj.status}", occurred_at=datetime.now(timezone.utc)))
    record_audit(db, organization_id=ident.organization_id, user_id=ident.user_id, entity_type="lead", entity_id=obj.id, action="status_change", new_values={"before": {"status": old}, "after": {"status": obj.status, "lost_reason": obj.lost_reason}})
    save(db); db.refresh(obj); return obj


@router.delete("/{lead_id}", status_code=204)
def archive_lead(lead_id: UUID, db: Session = Depends(get_db), ident: IdentityContext = Depends(require_permissions(PermissionCode.CRM_DELETE.value))):
    obj = get_lead(db, ident, lead_id); obj.deleted_at = datetime.now(timezone.utc)
    record_audit(db, organization_id=ident.organization_id, user_id=ident.user_id, entity_type="lead", entity_id=obj.id, action="soft_delete", new_values={"deleted_at": obj.deleted_at.isoformat()})
    save(db); return Response(status_code=204)


@router.get("/{lead_id}/timeline")
def timeline(lead_id: UUID, db: Session = Depends(get_db), ident: IdentityContext = Depends(require_permissions(PermissionCode.CRM_READ.value))):
    get_lead(db, ident, lead_id)
    interactions = list(db.scalars(select(LeadInteraction).where(LeadInteraction.lead_id == lead_id, LeadInteraction.organization_id == ident.organization_id).order_by(LeadInteraction.occurred_at.desc())))
    tasks = list(db.scalars(select(LeadTask).where(LeadTask.lead_id == lead_id, LeadTask.organization_id == ident.organization_id).order_by(LeadTask.due_at.desc())))
    proposals = list(db.scalars(select(LeadProposal).where(LeadProposal.lead_id == lead_id, LeadProposal.organization_id == ident.organization_id).order_by(LeadProposal.created_at.desc())))
    contracts = list(db.scalars(select(CommercialContract).where(CommercialContract.lead_id == lead_id, CommercialContract.organization_id == ident.organization_id, CommercialContract.deleted_at.is_(None)).order_by(CommercialContract.created_at.desc())))
    return {"interactions": interactions, "tasks": tasks, "proposals": proposals, "contracts": contracts}


@router.post("/{lead_id}/interactions", response_model=InteractionRead, status_code=201)
def add_interaction(lead_id: UUID, payload: InteractionCreate, db: Session = Depends(get_db), ident: IdentityContext = Depends(require_permissions(PermissionCode.CRM_CREATE.value))):
    lead = get_lead(db, ident, lead_id)
    obj = LeadInteraction(organization_id=ident.organization_id, lead_id=lead.id, user_id=ident.user_id, interaction_type=payload.interaction_type, description=payload.description, occurred_at=payload.occurred_at); db.add(obj)
    if lead.status == "NOVO" and payload.interaction_type != "STATUS":
        lead.status = "CONTATADO"
        db.add(LeadInteraction(organization_id=ident.organization_id, lead_id=lead.id, user_id=ident.user_id, interaction_type="STATUS", description="Lead avançado automaticamente para CONTATADO após a primeira interação", occurred_at=payload.occurred_at))
        record_audit(db, organization_id=ident.organization_id, user_id=ident.user_id, entity_type="lead", entity_id=lead.id, action="auto_status_change", new_values={"from": "NOVO", "to": "CONTATADO"})
    if payload.next_action and payload.next_action_at:
        validate_fk(db, ident, User, payload.assigned_to_id, "Responsável")
        db.add(LeadTask(organization_id=ident.organization_id, lead_id=lead.id, assigned_to_id=payload.assigned_to_id, description=payload.next_action, due_at=payload.next_action_at))
    db.flush(); record_audit(db, organization_id=ident.organization_id, user_id=ident.user_id, entity_type="lead_interaction", entity_id=obj.id, action="create", new_values={"lead_id": str(lead.id), "type": obj.interaction_type}); save(db); db.refresh(obj); return obj


@router.post("/{lead_id}/tasks", response_model=TaskRead, status_code=201)
def add_task(lead_id: UUID, payload: TaskCreate, db: Session = Depends(get_db), ident: IdentityContext = Depends(require_permissions(PermissionCode.CRM_CREATE.value))):
    lead = get_lead(db, ident, lead_id); validate_fk(db, ident, User, payload.assigned_to_id, "Responsável")
    obj = LeadTask(organization_id=ident.organization_id, lead_id=lead.id, **payload.model_dump()); db.add(obj); db.flush(); record_audit(db, organization_id=ident.organization_id, user_id=ident.user_id, entity_type="lead_task", entity_id=obj.id, action="create", new_values={"lead_id": str(lead.id)}); save(db); db.refresh(obj); return obj


@router.patch("/{lead_id}/tasks/{task_id}/complete", response_model=TaskRead)
def complete_task(lead_id: UUID, task_id: UUID, db: Session = Depends(get_db), ident: IdentityContext = Depends(require_permissions(PermissionCode.CRM_UPDATE.value))):
    get_lead(db, ident, lead_id); obj = db.scalar(select(LeadTask).where(LeadTask.id == task_id, LeadTask.lead_id == lead_id, LeadTask.organization_id == ident.organization_id))
    if not obj: raise HTTPException(404, "Tarefa não encontrada")
    obj.status = "CONCLUIDA"; obj.completed_at = datetime.now(timezone.utc)
    record_audit(db, organization_id=ident.organization_id, user_id=ident.user_id, entity_type="lead_task", entity_id=obj.id, action="complete", new_values={"status": "CONCLUIDA"})
    save(db); db.refresh(obj); return obj


@router.post("/{lead_id}/proposals", response_model=ProposalRead, status_code=201)
def add_proposal(lead_id: UUID, payload: ProposalCreate, db: Session = Depends(get_db), ident: IdentityContext = Depends(require_permissions(PermissionCode.CRM_CREATE.value))):
    lead = get_lead(db, ident, lead_id); obj = LeadProposal(organization_id=ident.organization_id, lead_id=lead.id, **payload.model_dump()); db.add(obj)
    if lead.status not in {"CONVERTIDO", "PERDIDO", "PROPOSTA"}:
        previous = lead.status; lead.status = "PROPOSTA"
        db.add(LeadInteraction(organization_id=ident.organization_id, lead_id=lead.id, user_id=ident.user_id, interaction_type="STATUS", description="Lead avançado automaticamente para PROPOSTA", occurred_at=datetime.now(timezone.utc)))
        record_audit(db, organization_id=ident.organization_id, user_id=ident.user_id, entity_type="lead", entity_id=lead.id, action="auto_status_change", new_values={"from": previous, "to": "PROPOSTA"})
    db.flush(); record_audit(db, organization_id=ident.organization_id, user_id=ident.user_id, entity_type="lead_proposal", entity_id=obj.id, action="create", new_values={"lead_id": str(lead.id), "value": str(obj.fixed_value)}); save(db); db.refresh(obj); return obj


@router.patch("/{lead_id}/proposals/{proposal_id}", response_model=ProposalRead)
def update_proposal(lead_id: UUID, proposal_id: UUID, payload: ProposalUpdate, db: Session = Depends(get_db), ident: IdentityContext = Depends(require_permissions(PermissionCode.CRM_UPDATE.value))):
    get_lead(db, ident, lead_id)
    obj = db.scalar(select(LeadProposal).where(LeadProposal.id == proposal_id, LeadProposal.lead_id == lead_id, LeadProposal.organization_id == ident.organization_id))
    if not obj: raise HTTPException(404, "Proposta não encontrada")
    previous = obj.status; obj.status = payload.status
    if payload.status == "ENVIADA" and not obj.sent_at: obj.sent_at = datetime.now(timezone.utc)
    record_audit(db, organization_id=ident.organization_id, user_id=ident.user_id, entity_type="lead_proposal", entity_id=obj.id, action="status_change", new_values={"from": previous, "to": obj.status})
    save(db); db.refresh(obj); return obj


@router.post("/{lead_id}/proposals/{proposal_id}/contract", response_model=ContractRead, status_code=201)
def create_contract(lead_id: UUID, proposal_id: UUID, payload: ContractCreate, db: Session = Depends(get_db), ident: IdentityContext = Depends(require_permissions(PermissionCode.CRM_CREATE.value))):
    lead = get_lead(db, ident, lead_id)
    proposal = db.scalar(select(LeadProposal).where(LeadProposal.id == proposal_id, LeadProposal.lead_id == lead_id, LeadProposal.organization_id == ident.organization_id))
    if not proposal: raise HTTPException(404, "Proposta não encontrada")
    if proposal.status != "ACEITA": raise HTTPException(422, "A proposta deve estar aceita antes de gerar o contrato")
    if not lead.client_id: raise HTTPException(422, "Converta o lead em cliente antes de gerar o contrato")
    existing = db.scalar(select(CommercialContract).where(CommercialContract.proposal_id == proposal_id, CommercialContract.deleted_at.is_(None)))
    if existing: return existing
    organization = db.get(Organization, ident.organization_id)
    client = db.get(Client, lead.client_id)
    service = db.get(ServiceType, lead.service_type_id)
    template = None
    if payload.template_id:
        template = db.scalar(select(ContractTemplate).where(ContractTemplate.id == payload.template_id, ContractTemplate.organization_id == ident.organization_id, ContractTemplate.active.is_(True), ContractTemplate.deleted_at.is_(None)))
        if not template: raise HTTPException(422, "Modelo de contrato não encontrado ou inativo")
        if template.service_type_id and template.service_type_id != lead.service_type_id: raise HTTPException(422, "Este modelo pertence a outro serviço")
    sequence = (db.scalar(select(func.count(CommercialContract.id)).where(CommercialContract.organization_id == ident.organization_id)) or 0) + 1
    number = f"CTR-{datetime.now(timezone.utc).year}-{sequence:05d}"
    obj = CommercialContract(
        organization_id=ident.organization_id, lead_id=lead.id, proposal_id=proposal.id, client_id=client.id,
        contract_number=number, template_id=template.id if template else None,
        title=payload.title or (template.title if template else "Contrato de prestação de serviços advocatícios"),
        content=payload.content or (render_contract_template(template.content, organization, client, service, proposal) if template else default_contract_content(organization, client, lead, proposal)), notes=payload.notes,
    )
    db.add(obj); db.flush()
    db.add(LeadInteraction(organization_id=ident.organization_id, lead_id=lead.id, user_id=ident.user_id, interaction_type="DOCUMENTO", description=f"Contrato {number} gerado", occurred_at=datetime.now(timezone.utc)))
    record_audit(db, organization_id=ident.organization_id, user_id=ident.user_id, entity_type="commercial_contract", entity_id=obj.id, action="create", new_values={"number": number, "proposal_id": str(proposal.id), "template_id": str(template.id) if template else None})
    save(db); db.refresh(obj); return obj


@router.patch("/{lead_id}/contracts/{contract_id}/status", response_model=ContractRead)
def update_contract_status(lead_id: UUID, contract_id: UUID, payload: ContractStatusUpdate, db: Session = Depends(get_db), ident: IdentityContext = Depends(require_permissions(PermissionCode.CRM_UPDATE.value))):
    get_lead(db, ident, lead_id)
    obj = db.scalar(select(CommercialContract).where(CommercialContract.id == contract_id, CommercialContract.lead_id == lead_id, CommercialContract.organization_id == ident.organization_id, CommercialContract.deleted_at.is_(None)))
    if not obj: raise HTTPException(404, "Contrato não encontrado")
    if payload.status == "APROVADO" and not (ident.is_superuser or str(ident.role).lower() in {"admin", "advogado"}):
        raise HTTPException(403, "Somente administrador ou advogado pode aprovar contratos")
    transitions = {"RASCUNHO": {"EM_REVISAO", "CANCELADO"}, "EM_REVISAO": {"APROVADO", "CANCELADO"}, "APROVADO": {"ENVIADO", "CANCELADO"}, "ENVIADO": {"ASSINADO", "CANCELADO"}, "ASSINADO": set(), "CANCELADO": set()}
    if payload.status not in transitions.get(obj.status, set()): raise HTTPException(409, f"Transição inválida de {obj.status} para {payload.status}")
    previous = obj.status; now = datetime.now(timezone.utc); obj.status = payload.status
    if payload.status == "APROVADO": obj.approved_by_id = ident.user_id; obj.approved_at = now
    if payload.status == "ENVIADO": obj.sent_at = now
    if payload.status == "ASSINADO": obj.signed_at = now; obj.signature_reference = payload.signature_reference
    db.add(LeadInteraction(organization_id=ident.organization_id, lead_id=lead_id, user_id=ident.user_id, interaction_type="DOCUMENTO", description=f"Contrato {obj.contract_number}: {previous} → {obj.status}", occurred_at=now))
    record_audit(db, organization_id=ident.organization_id, user_id=ident.user_id, entity_type="commercial_contract", entity_id=obj.id, action="status_change", new_values={"from": previous, "to": obj.status, "signature_reference": obj.signature_reference})
    save(db); db.refresh(obj); return obj


@router.get("/{lead_id}/contracts/{contract_id}/document", response_class=Response)
def contract_document(lead_id: UUID, contract_id: UUID, db: Session = Depends(get_db), ident: IdentityContext = Depends(require_permissions(PermissionCode.CRM_READ.value))):
    get_lead(db, ident, lead_id)
    obj = db.scalar(select(CommercialContract).where(CommercialContract.id == contract_id, CommercialContract.lead_id == lead_id, CommercialContract.organization_id == ident.organization_id, CommercialContract.deleted_at.is_(None)))
    if not obj: raise HTTPException(404, "Contrato não encontrado")
    content = "<br>".join(escape(obj.content).splitlines())
    html = f"<!doctype html><html lang='pt-BR'><head><meta charset='utf-8'><title>{escape(obj.contract_number)}</title><style>body{{font:16px Georgia,serif;line-height:1.6;max-width:800px;margin:48px auto;padding:0 24px;color:#17231d}}h1{{font-size:24px}}.meta{{color:#657269}}@media print{{button{{display:none}}body{{margin:0}}}}</style></head><body><button onclick='print()'>Imprimir / salvar em PDF</button><p class='meta'>{escape(obj.contract_number)} · versão {obj.version} · {escape(obj.status)}</p><h1>{escape(obj.title)}</h1><div>{content}</div></body></html>"
    return Response(html, media_type="text/html")


@router.post("/{lead_id}/convert", response_model=ConversionResult)
def convert(lead_id: UUID, payload: ConvertLead, db: Session = Depends(get_db), ident: IdentityContext = Depends(require_permissions(PermissionCode.CRM_CONVERT.value))):
    lead = get_lead(db, ident, lead_id)
    if lead.client_id:
        if payload.create_recovery_case and not lead.recovery_case_id:
            service = db.get(ServiceType, lead.service_type_id)
            if not service or service.code != "CS_RECUPERA":
                raise HTTPException(422, "RecoveryCase só pode ser aberto para o serviço CS Recupera")
            case = create_case(db, ident.organization_id, RecoveryCaseCreate(client_id=lead.client_id, source=RecoveryCaseSource.API, assigned_user_id=lead.owner_id, notes=f"Originado posteriormente do lead {lead.id}"))
            lead.recovery_case_id = case.id
            db.add(LeadInteraction(organization_id=ident.organization_id, lead_id=lead.id, user_id=ident.user_id, interaction_type="STATUS", description="Caso CS Recupera aberto após a conversão", occurred_at=datetime.now(timezone.utc)))
            record_audit(db, organization_id=ident.organization_id, user_id=ident.user_id, entity_type="lead", entity_id=lead.id, action="create_recovery_case_after_conversion", new_values={"recovery_case_id": str(case.id)})
        if lead.status != "CONVERTIDO":
            lead.status = "CONVERTIDO"
            lead.converted_at = lead.converted_at or datetime.now(timezone.utc)
            lead.converted_by_id = lead.converted_by_id or ident.user_id
            db.add(LeadInteraction(organization_id=ident.organization_id, lead_id=lead.id, user_id=ident.user_id, interaction_type="STATUS", description="Status de conversão sincronizado", occurred_at=datetime.now(timezone.utc)))
            record_audit(db, organization_id=ident.organization_id, user_id=ident.user_id, entity_type="lead", entity_id=lead.id, action="conversion_status_sync", new_values={"status": "CONVERTIDO"})
        if db.is_modified(lead):
            save(db); db.refresh(lead)
        return ConversionResult(lead=lead, client_id=lead.client_id, recovery_case_id=lead.recovery_case_id)
    conditions = []
    if lead.cpf: conditions.append(Client.cpf == lead.cpf)
    if lead.phone: conditions.append(Client.phone == lead.phone)
    if lead.whatsapp: conditions.append(Client.phone == lead.whatsapp)
    if lead.email: conditions.append(func.lower(Client.email) == lead.email.lower())
    duplicates = list(db.scalars(select(Client).where(Client.organization_id == ident.organization_id, Client.archived_at.is_(None), or_(*conditions)))) if conditions else []
    if duplicates and not payload.confirm_duplicate_client_id:
        raise HTTPException(409, detail={"message": "Possível cliente duplicado", "client_ids": [str(c.id) for c in duplicates]})
    if payload.confirm_duplicate_client_id:
        client = db.scalar(select(Client).where(Client.id == payload.confirm_duplicate_client_id, Client.organization_id == ident.organization_id))
        if not client: raise HTTPException(422, "Cliente indicado não encontrado")
    else:
        if not lead.cpf: raise HTTPException(422, "CPF é obrigatório para criar Cliente na estrutura atual")
        client = Client(organization_id=ident.organization_id, assigned_user_id=lead.owner_id, full_name=lead.full_name, cpf=lead.cpf, birth_date=lead.birth_date, email=lead.email, phone=lead.whatsapp or lead.phone, city=lead.city, state=lead.state, status="contracted", notes=lead.initial_notes)
        db.add(client); db.flush()
    case_id = None
    service = db.get(ServiceType, lead.service_type_id)
    if payload.create_recovery_case:
        if not service or service.code != "CS_RECUPERA": raise HTTPException(422, "RecoveryCase só pode ser aberto para o serviço CS Recupera")
        case = create_case(db, ident.organization_id, RecoveryCaseCreate(client_id=client.id, source=RecoveryCaseSource.API, assigned_user_id=lead.owner_id, notes=f"Originado do lead {lead.id}")); case_id = case.id
    lead.status = "CONVERTIDO"; lead.converted_at = datetime.now(timezone.utc); lead.converted_by_id = ident.user_id; lead.client_id = client.id; lead.recovery_case_id = case_id
    db.add(LeadInteraction(organization_id=ident.organization_id, lead_id=lead.id, user_id=ident.user_id, interaction_type="STATUS", description="Lead convertido em Cliente" + (" e RecoveryCase" if case_id else ""), occurred_at=lead.converted_at))
    record_audit(db, organization_id=ident.organization_id, user_id=ident.user_id, entity_type="lead", entity_id=lead.id, action="convert", new_values={"client_id": str(client.id), "recovery_case_id": str(case_id) if case_id else None})
    save(db); db.refresh(lead); return ConversionResult(lead=lead, client_id=client.id, recovery_case_id=case_id)


def period_filters(org, date_from, date_to):
    filters = [Lead.organization_id == org, Lead.deleted_at.is_(None)]
    if date_from: filters.append(Lead.created_at >= date_from)
    if date_to: filters.append(Lead.created_at <= date_to)
    return filters


@router.get("/analytics/dashboard", response_model=DashboardRead)
def dashboard(date_from: datetime | None = None, date_to: datetime | None = None, owner_id: UUID | None = None, source_id: UUID | None = None, service_type_id: UUID | None = None, db: Session = Depends(get_db), ident: IdentityContext = Depends(require_permissions(PermissionCode.CRM_READ.value))):
    filters = period_filters(ident.organization_id, date_from, date_to)
    if owner_id: filters.append(Lead.owner_id == owner_id)
    if source_id: filters.append(Lead.source_id == source_id)
    if service_type_id: filters.append(Lead.service_type_id == service_type_id)
    counts = dict(db.execute(select(Lead.status, func.count()).where(*filters).group_by(Lead.status)).all()); total = sum(counts.values()); converted = counts.get("CONVERTIDO", 0)
    avg = db.scalar(select(func.avg(func.extract("epoch", Lead.converted_at - Lead.created_at) / 86400)).where(*filters, Lead.converted_at.is_not(None))) or 0
    estimated = db.scalar(select(func.coalesce(func.sum(LeadProposal.fixed_value), 0)).join(Lead, Lead.id == LeadProposal.lead_id).where(*filters, LeadProposal.status.in_(["RASCUNHO", "ENVIADA"]))) or 0
    contracted = db.scalar(select(func.coalesce(func.sum(LeadProposal.fixed_value), 0)).join(Lead, Lead.id == LeadProposal.lead_id).where(*filters, LeadProposal.status == "ACEITA")) or 0
    now = datetime.now(timezone.utc); today = now.date()
    overdue_tasks = db.scalar(select(func.count(LeadTask.id)).join(Lead, Lead.id == LeadTask.lead_id).where(*filters, LeadTask.status == "PENDENTE", LeadTask.due_at < now)) or 0
    proposals_expiring = db.scalar(select(func.count(LeadProposal.id)).join(Lead, Lead.id == LeadProposal.lead_id).where(*filters, LeadProposal.status.in_(["RASCUNHO", "ENVIADA"]), LeadProposal.valid_until >= today, LeadProposal.valid_until <= today + timedelta(days=3))) or 0
    future_task = select(LeadTask.id).where(LeadTask.lead_id == Lead.id, LeadTask.status == "PENDENTE", LeadTask.due_at >= now).exists()
    leads_without_next_action = db.scalar(select(func.count(Lead.id)).where(*filters, Lead.status.in_(["NOVO", "CONTATADO", "QUALIFICADO", "PROPOSTA"]), ~future_task)) or 0
    return DashboardRead(new_leads=counts.get("NOVO",0), in_progress=sum(counts.get(x,0) for x in ["NOVO","CONTATADO","QUALIFICADO","PROPOSTA"]), qualified=counts.get("QUALIFICADO",0), open_proposals=counts.get("PROPOSTA",0), converted=converted, lost=counts.get("PERDIDO",0), conversion_rate=round(converted*100/total,2) if total else 0, average_conversion_days=round(float(avg),2), estimated_revenue=float(estimated), contracted_revenue=float(contracted), overdue_tasks=overdue_tasks, proposals_expiring=proposals_expiring, leads_without_next_action=leads_without_next_action)


@router.get("/analytics/reports")
def reports(db: Session = Depends(get_db), ident: IdentityContext = Depends(require_permissions(PermissionCode.CRM_READ.value))):
    org = ident.organization_id
    def grouped(key, name, join):
        rows = db.execute(select(key, name, func.count(Lead.id), func.sum(func.cast(Lead.status == "CONVERTIDO", Integer)), func.sum(func.cast(Lead.status == "PERDIDO", Integer))).select_from(Lead).join(join).where(Lead.organization_id == org, Lead.deleted_at.is_(None)).group_by(key, name)).all()
        return [ReportRow(key=str(r[0]), name=r[1], leads=r[2], converted=r[3] or 0, lost=r[4] or 0, conversion_rate=round((r[3] or 0)*100/r[2],2) if r[2] else 0) for r in rows]
    by_source = grouped(LeadSource.id, LeadSource.name, LeadSource); by_service = grouped(ServiceType.id, ServiceType.name, ServiceType)
    owner_rows = db.execute(select(User.id, User.full_name, func.count(Lead.id), func.sum(func.cast(Lead.status == "CONVERTIDO", Integer)), func.sum(func.cast(Lead.status == "PERDIDO", Integer))).select_from(Lead).join(User, User.id == Lead.owner_id).where(Lead.organization_id == org, Lead.deleted_at.is_(None)).group_by(User.id, User.full_name)).all()
    by_owner = [ReportRow(key=str(r[0]), name=r[1], leads=r[2], converted=r[3] or 0, lost=r[4] or 0, conversion_rate=round((r[3] or 0)*100/r[2],2) if r[2] else 0) for r in owner_rows]
    return {"by_source": by_source, "by_service": by_service, "by_owner": by_owner}