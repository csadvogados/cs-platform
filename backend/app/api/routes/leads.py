from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy import Integer, func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.deps import get_identity_context
from app.db.session import get_db
from app.models.client import Client
from app.models.crm import Lead, LeadInteraction, LeadProposal, LeadSource, LeadTask, ServiceType
from app.models.recovery import RecoveryCaseSource
from app.models.user import User
from app.schemas.leads import *
from app.schemas.recovery import RecoveryCaseCreate
from app.security.identity import IdentityContext
from app.services.audit import record_audit
from app.services.recovery_cases import create_case

router = APIRouter()
ALLOWED_ROLES = {"admin", "supervisor", "advogado", "atendimento"}
DEFAULT_SOURCES = [("INDICACAO","Indicação"),("INSTAGRAM","Instagram"),("FACEBOOK","Facebook"),("GOOGLE","Google"),("WHATSAPP","WhatsApp"),("SITE","Site"),("CLIENTE_ANTIGO","Cliente antigo"),("PARCEIRO","Parceiro"),("EVENTO","Evento"),("PROSPECCAO_PERMITIDA","Prospecção permitida"),("OUTRO","Outro")]
DEFAULT_SERVICES = [("CS_RECUPERA","CS Recupera"),("CONSUMIDOR","Consumidor"),("BANCARIO","Bancário"),("PREVIDENCIARIO","Previdenciário"),("FAMILIA","Família"),("INVENTARIO","Inventário / Sucessões"),("TRABALHISTA","Trabalhista"),("CRIMINAL","Criminal"),("ENERGIA","Energia"),("CONSULTORIA","Consultoria"),("CS_CAPTA_RECURSOS","CS Capta Recursos"),("OUTRO","Outro")]


def authorize(ident: IdentityContext):
    if not ident.is_superuser and ident.role not in ALLOWED_ROLES:
        raise HTTPException(403, "Perfil sem acesso ao core comercial")


def get_lead(db: Session, ident: IdentityContext, lead_id: UUID) -> Lead:
    authorize(ident)
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


def ensure_catalogs(db: Session, organization_id: UUID):
    if not db.scalar(select(LeadSource.id).where(LeadSource.organization_id == organization_id).limit(1)):
        db.add_all([LeadSource(organization_id=organization_id, code=code, name=name) for code, name in DEFAULT_SOURCES])
    if not db.scalar(select(ServiceType.id).where(ServiceType.organization_id == organization_id).limit(1)):
        db.add_all([ServiceType(organization_id=organization_id, code=code, name=name) for code, name in DEFAULT_SERVICES])
    db.flush()


@router.get("/catalogs")
def catalogs(db: Session = Depends(get_db), ident: IdentityContext = Depends(get_identity_context)):
    authorize(ident)
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
               db: Session = Depends(get_db), ident: IdentityContext = Depends(get_identity_context)):
    authorize(ident); filters = [Lead.organization_id == ident.organization_id, Lead.deleted_at.is_(None)]
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
def create_lead(payload: LeadCreate, db: Session = Depends(get_db), ident: IdentityContext = Depends(get_identity_context)):
    authorize(ident); validate_fk(db, ident, LeadSource, payload.source_id, "Origem"); validate_fk(db, ident, ServiceType, payload.service_type_id, "Serviço"); validate_fk(db, ident, User, payload.owner_id, "Responsável")
    obj = Lead(organization_id=ident.organization_id, **payload.model_dump())
    db.add(obj); db.flush()
    db.add(LeadInteraction(organization_id=ident.organization_id, lead_id=obj.id, user_id=ident.user_id, interaction_type="STATUS", description="Lead criado com status NOVO", occurred_at=datetime.now(timezone.utc)))
    record_audit(db, organization_id=ident.organization_id, user_id=ident.user_id, entity_type="lead", entity_id=obj.id, action="create", new_values={"name": obj.full_name, "status": obj.status})
    save(db); db.refresh(obj); return obj


@router.get("/{lead_id}", response_model=LeadRead)
def read_lead(lead_id: UUID, db: Session = Depends(get_db), ident: IdentityContext = Depends(get_identity_context)): return get_lead(db, ident, lead_id)


@router.patch("/{lead_id}", response_model=LeadRead)
def update_lead(lead_id: UUID, payload: LeadUpdate, db: Session = Depends(get_db), ident: IdentityContext = Depends(get_identity_context)):
    obj = get_lead(db, ident, lead_id); changes = payload.model_dump(exclude_unset=True)
    for field, model, label in (("source_id", LeadSource, "Origem"), ("service_type_id", ServiceType, "Serviço"), ("owner_id", User, "Responsável")):
        if field in changes: validate_fk(db, ident, model, changes[field], label)
    before = {key: str(getattr(obj, key)) for key in changes}
    for key, value in changes.items(): setattr(obj, key, value)
    record_audit(db, organization_id=ident.organization_id, user_id=ident.user_id, entity_type="lead", entity_id=obj.id, action="update", new_values={"before": before, "after": {k: str(v) for k, v in changes.items()}})
    save(db); db.refresh(obj); return obj


@router.post("/{lead_id}/status", response_model=LeadRead)
def change_status(lead_id: UUID, payload: StatusChange, db: Session = Depends(get_db), ident: IdentityContext = Depends(get_identity_context)):
    obj = get_lead(db, ident, lead_id)
    if payload.status == "CONVERTIDO": raise HTTPException(422, "Use o endpoint de conversão")
    old = obj.status; obj.status = payload.status
    obj.lost_reason = payload.lost_reason if payload.status == "PERDIDO" else None; obj.lost_notes = payload.lost_notes if payload.status == "PERDIDO" else None
    db.add(LeadInteraction(organization_id=ident.organization_id, lead_id=obj.id, user_id=ident.user_id, interaction_type="STATUS", description=f"Status alterado de {old} para {obj.status}", occurred_at=datetime.now(timezone.utc)))
    record_audit(db, organization_id=ident.organization_id, user_id=ident.user_id, entity_type="lead", entity_id=obj.id, action="status_change", new_values={"before": {"status": old}, "after": {"status": obj.status, "lost_reason": obj.lost_reason}})
    save(db); db.refresh(obj); return obj


@router.delete("/{lead_id}", status_code=204)
def archive_lead(lead_id: UUID, db: Session = Depends(get_db), ident: IdentityContext = Depends(get_identity_context)):
    obj = get_lead(db, ident, lead_id); obj.deleted_at = datetime.now(timezone.utc)
    record_audit(db, organization_id=ident.organization_id, user_id=ident.user_id, entity_type="lead", entity_id=obj.id, action="soft_delete", new_values={"deleted_at": obj.deleted_at.isoformat()})
    save(db); return Response(status_code=204)


@router.get("/{lead_id}/timeline")
def timeline(lead_id: UUID, db: Session = Depends(get_db), ident: IdentityContext = Depends(get_identity_context)):
    get_lead(db, ident, lead_id)
    interactions = list(db.scalars(select(LeadInteraction).where(LeadInteraction.lead_id == lead_id, LeadInteraction.organization_id == ident.organization_id).order_by(LeadInteraction.occurred_at.desc())))
    tasks = list(db.scalars(select(LeadTask).where(LeadTask.lead_id == lead_id, LeadTask.organization_id == ident.organization_id).order_by(LeadTask.due_at.desc())))
    proposals = list(db.scalars(select(LeadProposal).where(LeadProposal.lead_id == lead_id, LeadProposal.organization_id == ident.organization_id).order_by(LeadProposal.created_at.desc())))
    return {"interactions": interactions, "tasks": tasks, "proposals": proposals}


@router.post("/{lead_id}/interactions", response_model=InteractionRead, status_code=201)
def add_interaction(lead_id: UUID, payload: InteractionCreate, db: Session = Depends(get_db), ident: IdentityContext = Depends(get_identity_context)):
    lead = get_lead(db, ident, lead_id)
    obj = LeadInteraction(organization_id=ident.organization_id, lead_id=lead.id, user_id=ident.user_id, interaction_type=payload.interaction_type, description=payload.description, occurred_at=payload.occurred_at); db.add(obj)
    if payload.next_action and payload.next_action_at:
        validate_fk(db, ident, User, payload.assigned_to_id, "Responsável")
        db.add(LeadTask(organization_id=ident.organization_id, lead_id=lead.id, assigned_to_id=payload.assigned_to_id, description=payload.next_action, due_at=payload.next_action_at))
    db.flush(); record_audit(db, organization_id=ident.organization_id, user_id=ident.user_id, entity_type="lead_interaction", entity_id=obj.id, action="create", new_values={"lead_id": str(lead.id), "type": obj.interaction_type}); save(db); db.refresh(obj); return obj


@router.post("/{lead_id}/tasks", response_model=TaskRead, status_code=201)
def add_task(lead_id: UUID, payload: TaskCreate, db: Session = Depends(get_db), ident: IdentityContext = Depends(get_identity_context)):
    lead = get_lead(db, ident, lead_id); validate_fk(db, ident, User, payload.assigned_to_id, "Responsável")
    obj = LeadTask(organization_id=ident.organization_id, lead_id=lead.id, **payload.model_dump()); db.add(obj); db.flush(); record_audit(db, organization_id=ident.organization_id, user_id=ident.user_id, entity_type="lead_task", entity_id=obj.id, action="create", new_values={"lead_id": str(lead.id)}); save(db); db.refresh(obj); return obj


@router.patch("/{lead_id}/tasks/{task_id}/complete", response_model=TaskRead)
def complete_task(lead_id: UUID, task_id: UUID, db: Session = Depends(get_db), ident: IdentityContext = Depends(get_identity_context)):
    get_lead(db, ident, lead_id); obj = db.scalar(select(LeadTask).where(LeadTask.id == task_id, LeadTask.lead_id == lead_id, LeadTask.organization_id == ident.organization_id))
    if not obj: raise HTTPException(404, "Tarefa não encontrada")
    obj.status = "CONCLUIDA"; obj.completed_at = datetime.now(timezone.utc); save(db); db.refresh(obj); return obj


@router.post("/{lead_id}/proposals", response_model=ProposalRead, status_code=201)
def add_proposal(lead_id: UUID, payload: ProposalCreate, db: Session = Depends(get_db), ident: IdentityContext = Depends(get_identity_context)):
    lead = get_lead(db, ident, lead_id); obj = LeadProposal(organization_id=ident.organization_id, lead_id=lead.id, **payload.model_dump()); db.add(obj)
    if lead.status not in {"CONVERTIDO", "PERDIDO"}: lead.status = "PROPOSTA"
    db.flush(); record_audit(db, organization_id=ident.organization_id, user_id=ident.user_id, entity_type="lead_proposal", entity_id=obj.id, action="create", new_values={"lead_id": str(lead.id), "value": str(obj.fixed_value)}); save(db); db.refresh(obj); return obj


@router.post("/{lead_id}/convert", response_model=ConversionResult)
def convert(lead_id: UUID, payload: ConvertLead, db: Session = Depends(get_db), ident: IdentityContext = Depends(get_identity_context)):
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
def dashboard(date_from: datetime | None = None, date_to: datetime | None = None, owner_id: UUID | None = None, source_id: UUID | None = None, service_type_id: UUID | None = None, db: Session = Depends(get_db), ident: IdentityContext = Depends(get_identity_context)):
    authorize(ident); filters = period_filters(ident.organization_id, date_from, date_to)
    if owner_id: filters.append(Lead.owner_id == owner_id)
    if source_id: filters.append(Lead.source_id == source_id)
    if service_type_id: filters.append(Lead.service_type_id == service_type_id)
    counts = dict(db.execute(select(Lead.status, func.count()).where(*filters).group_by(Lead.status)).all()); total = sum(counts.values()); converted = counts.get("CONVERTIDO", 0)
    avg = db.scalar(select(func.avg(func.extract("epoch", Lead.converted_at - Lead.created_at) / 86400)).where(*filters, Lead.converted_at.is_not(None))) or 0
    estimated = db.scalar(select(func.coalesce(func.sum(LeadProposal.fixed_value), 0)).join(Lead, Lead.id == LeadProposal.lead_id).where(*filters, LeadProposal.status.in_(["RASCUNHO", "ENVIADA"]))) or 0
    contracted = db.scalar(select(func.coalesce(func.sum(LeadProposal.fixed_value), 0)).join(Lead, Lead.id == LeadProposal.lead_id).where(*filters, LeadProposal.status == "ACEITA")) or 0
    return DashboardRead(new_leads=counts.get("NOVO",0), in_progress=sum(counts.get(x,0) for x in ["NOVO","CONTATADO","QUALIFICADO","PROPOSTA"]), qualified=counts.get("QUALIFICADO",0), open_proposals=counts.get("PROPOSTA",0), converted=converted, lost=counts.get("PERDIDO",0), conversion_rate=round(converted*100/total,2) if total else 0, average_conversion_days=round(float(avg),2), estimated_revenue=float(estimated), contracted_revenue=float(contracted))


@router.get("/analytics/reports")
def reports(db: Session = Depends(get_db), ident: IdentityContext = Depends(get_identity_context)):
    authorize(ident); org = ident.organization_id
    def grouped(key, name, join):
        rows = db.execute(select(key, name, func.count(Lead.id), func.sum(func.cast(Lead.status == "CONVERTIDO", Integer)), func.sum(func.cast(Lead.status == "PERDIDO", Integer))).select_from(Lead).join(join).where(Lead.organization_id == org, Lead.deleted_at.is_(None)).group_by(key, name)).all()
        return [ReportRow(key=str(r[0]), name=r[1], leads=r[2], converted=r[3] or 0, lost=r[4] or 0, conversion_rate=round((r[3] or 0)*100/r[2],2) if r[2] else 0) for r in rows]
    by_source = grouped(LeadSource.id, LeadSource.name, LeadSource); by_service = grouped(ServiceType.id, ServiceType.name, ServiceType)
    owner_rows = db.execute(select(User.id, User.full_name, func.count(Lead.id), func.sum(func.cast(Lead.status == "CONVERTIDO", Integer)), func.sum(func.cast(Lead.status == "PERDIDO", Integer))).select_from(Lead).join(User, User.id == Lead.owner_id).where(Lead.organization_id == org, Lead.deleted_at.is_(None)).group_by(User.id, User.full_name)).all()
    by_owner = [ReportRow(key=str(r[0]), name=r[1], leads=r[2], converted=r[3] or 0, lost=r[4] or 0, conversion_rate=round((r[3] or 0)*100/r[2],2) if r[2] else 0) for r in owner_rows]
    return {"by_source": by_source, "by_service": by_service, "by_owner": by_owner}
