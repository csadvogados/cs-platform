from datetime import date, datetime, timezone
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from sqlalchemy import func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.deps import get_identity_context
from app.db.session import get_db
from app.models.client import Client
from app.models.crm import CommercialContract, ContractDelivery, ContractTemplate, Lead, LeadInteraction, ServiceType
from app.schemas.leads import ContractDeliveryCreate, ContractDeliveryRead, ContractListItem, ContractRead, ContractSummary, ContractTemplateCreate, ContractTemplateRead, ContractTemplateUpdate
from app.security.identity import IdentityContext
from app.services.audit import record_audit

router = APIRouter()


@router.delete("/{contract_id}", status_code=204, summary="Arquivar contrato (administrador)")
def archive_contract(contract_id: UUID, db: Session = Depends(get_db), identity: IdentityContext = Depends(get_identity_context)):
    if not identity.is_superuser and str(identity.role).lower() != "admin":
        raise HTTPException(403, "Somente administrador pode arquivar contratos")
    obj = db.scalar(select(CommercialContract).where(
        CommercialContract.id == contract_id,
        CommercialContract.organization_id == identity.organization_id,
    ).with_for_update())
    if not obj:
        raise HTTPException(404, "Contrato não encontrado")
    if obj.deleted_at is None:
        now = datetime.now(timezone.utc)
        obj.deleted_at = now
        db.add(LeadInteraction(organization_id=identity.organization_id, lead_id=obj.lead_id,
            user_id=identity.user_id, interaction_type="DOCUMENTO", occurred_at=now,
            description=f"Contrato {obj.contract_number} arquivado. Documento e situação preservados."))
        record_audit(db, organization_id=identity.organization_id, user_id=identity.user_id,
            entity_type="commercial_contract", entity_id=obj.id, action="archive",
            new_values={"deleted_at": now.isoformat(), "status": obj.status, "contract_number": obj.contract_number})
        save(db)
    return Response(status_code=204)

ALLOWED_ROLES = {"admin", "supervisor", "advogado", "atendimento"}
TEMPLATE_MANAGER_ROLES = {"admin", "supervisor", "advogado"}
DEFAULT_TEMPLATE_CONTENT = """CONTRATO DE PRESTAÇÃO DE SERVIÇOS ADVOCATÍCIOS

CONTRATADA: {{escritorio}}.
CONTRATANTE: {{cliente_nome}}, CPF {{cliente_cpf}}.

OBJETO: prestação de serviços jurídicos de {{servico}}, conforme a proposta comercial vinculada.

HONORÁRIOS: valor fixo de {{valor_fixo}}; entrada de {{entrada}}; {{parcelas}} parcela(s) de {{valor_parcela}}; êxito de {{percentual_exito}}%.

As condições específicas, obrigações das partes, vigência e hipóteses de rescisão deverão ser revisadas antes da aprovação.

Ao aprovar este documento, a equipe confirma que o conteúdo foi revisado. O registro de assinatura nesta plataforma é manual."""


def authorize(identity: IdentityContext):
    if not identity.is_superuser and str(identity.role).lower() not in ALLOWED_ROLES:
        raise HTTPException(403, "Perfil sem acesso aos contratos comerciais")


def authorize_template_manager(identity: IdentityContext):
    authorize(identity)
    if not identity.is_superuser and str(identity.role).lower() not in TEMPLATE_MANAGER_ROLES:
        raise HTTPException(403, "Perfil sem permissão para alterar modelos de contrato")


def validate_service(db: Session, identity: IdentityContext, service_type_id: UUID | None):
    if service_type_id and not db.scalar(select(ServiceType.id).where(ServiceType.id == service_type_id, ServiceType.organization_id == identity.organization_id)):
        raise HTTPException(422, "Serviço não pertence à organização")


def save(db: Session):
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(409, "Já existe um modelo com este nome") from exc


def ensure_default_template(db: Session, identity: IdentityContext):
    existing = db.scalar(select(ContractTemplate.id).where(ContractTemplate.organization_id == identity.organization_id, ContractTemplate.deleted_at.is_(None)).limit(1))
    if existing:
        return
    db.add(ContractTemplate(organization_id=identity.organization_id, name="Prestação de serviços advocatícios", title="Contrato de prestação de serviços advocatícios", content=DEFAULT_TEMPLATE_CONTENT, created_by_id=identity.user_id))
    db.commit()


@router.get("/templates", response_model=list[ContractTemplateRead])
def list_templates(active_only: bool = True, db: Session = Depends(get_db), identity: IdentityContext = Depends(get_identity_context)):
    authorize(identity)
    ensure_default_template(db, identity)
    conditions = [ContractTemplate.organization_id == identity.organization_id, ContractTemplate.deleted_at.is_(None)]
    if active_only:
        conditions.append(ContractTemplate.active.is_(True))
    return list(db.scalars(select(ContractTemplate).where(*conditions).order_by(ContractTemplate.name)))


@router.post("/templates", response_model=ContractTemplateRead, status_code=201)
def create_template(payload: ContractTemplateCreate, db: Session = Depends(get_db), identity: IdentityContext = Depends(get_identity_context)):
    authorize_template_manager(identity)
    validate_service(db, identity, payload.service_type_id)
    obj = ContractTemplate(id=uuid4(), organization_id=identity.organization_id, created_by_id=identity.user_id, **payload.model_dump())
    db.add(obj)
    record_audit(db, organization_id=identity.organization_id, user_id=identity.user_id, entity_type="contract_template", entity_id=obj.id, action="create", new_values={"name": obj.name})
    save(db)
    db.refresh(obj)
    return obj


@router.patch("/templates/{template_id}", response_model=ContractTemplateRead)
def update_template(template_id: UUID, payload: ContractTemplateUpdate, db: Session = Depends(get_db), identity: IdentityContext = Depends(get_identity_context)):
    authorize_template_manager(identity)
    obj = db.scalar(select(ContractTemplate).where(ContractTemplate.id == template_id, ContractTemplate.organization_id == identity.organization_id, ContractTemplate.deleted_at.is_(None)))
    if not obj:
        raise HTTPException(404, "Modelo não encontrado")
    changes = payload.model_dump(exclude_unset=True)
    if "service_type_id" in changes:
        validate_service(db, identity, changes["service_type_id"])
    for key, value in changes.items():
        setattr(obj, key, value)
    record_audit(db, organization_id=identity.organization_id, user_id=identity.user_id, entity_type="contract_template", entity_id=obj.id, action="update", new_values={"fields": list(changes)})
    save(db)
    db.refresh(obj)
    return obj


@router.delete("/templates/{template_id}", status_code=204)
def delete_template(template_id: UUID, db: Session = Depends(get_db), identity: IdentityContext = Depends(get_identity_context)):
    authorize_template_manager(identity)
    obj = db.scalar(select(ContractTemplate).where(ContractTemplate.id == template_id, ContractTemplate.organization_id == identity.organization_id, ContractTemplate.deleted_at.is_(None)))
    if not obj:
        raise HTTPException(404, "Modelo não encontrado")
    remaining = db.scalar(select(func.count(ContractTemplate.id)).where(ContractTemplate.organization_id == identity.organization_id, ContractTemplate.id != template_id, ContractTemplate.deleted_at.is_(None))) or 0
    if remaining == 0:
        raise HTTPException(409, "Mantenha pelo menos um modelo de contrato cadastrado")
    obj.deleted_at = datetime.now(timezone.utc)
    record_audit(db, organization_id=identity.organization_id, user_id=identity.user_id, entity_type="contract_template", entity_id=obj.id, action="delete", new_values={"name": obj.name})
    save(db)


@router.get("/{contract_id}/deliveries", response_model=list[ContractDeliveryRead])
def list_deliveries(contract_id: UUID, db: Session = Depends(get_db), identity: IdentityContext = Depends(get_identity_context)):
    authorize(identity)
    contract = db.scalar(select(CommercialContract.id).where(CommercialContract.id == contract_id, CommercialContract.organization_id == identity.organization_id, CommercialContract.deleted_at.is_(None)))
    if not contract:
        raise HTTPException(404, "Contrato não encontrado")
    return list(db.scalars(select(ContractDelivery).where(ContractDelivery.contract_id == contract_id, ContractDelivery.organization_id == identity.organization_id).order_by(ContractDelivery.sent_at.desc())))


@router.post("/{contract_id}/deliveries", response_model=ContractDeliveryRead, status_code=201)
def register_delivery(contract_id: UUID, payload: ContractDeliveryCreate, db: Session = Depends(get_db), identity: IdentityContext = Depends(get_identity_context)):
    authorize(identity)
    contract = db.scalar(select(CommercialContract).where(CommercialContract.id == contract_id, CommercialContract.organization_id == identity.organization_id, CommercialContract.deleted_at.is_(None)))
    if not contract:
        raise HTTPException(404, "Contrato não encontrado")
    if contract.status not in {"APROVADO", "ENVIADO"}:
        raise HTTPException(409, "O contrato deve estar aprovado antes do envio")
    if payload.signature_due_at < date.today():
        raise HTTPException(422, "O prazo para assinatura não pode estar no passado")
    now = datetime.now(timezone.utc)
    delivery = ContractDelivery(id=uuid4(), organization_id=identity.organization_id, contract_id=contract.id, sent_by_id=identity.user_id, sent_at=now, **payload.model_dump())
    contract.status = "ENVIADO"
    contract.sent_at = now
    contract.signature_due_at = payload.signature_due_at
    contract.delivery_channel = payload.channel
    contract.delivery_recipient = payload.recipient
    db.add(delivery)
    db.add(LeadInteraction(organization_id=identity.organization_id, lead_id=contract.lead_id, user_id=identity.user_id, interaction_type="DOCUMENTO", description=f"Contrato {contract.contract_number} enviado por {payload.channel} para {payload.recipient}", occurred_at=now))
    record_audit(db, organization_id=identity.organization_id, user_id=identity.user_id, entity_type="commercial_contract", entity_id=contract.id, action="send", new_values={"channel": payload.channel, "recipient": payload.recipient, "signature_due_at": str(payload.signature_due_at)})
    save(db)
    db.refresh(delivery)
    return delivery


@router.get("/summary", response_model=ContractSummary)
def summary(db: Session = Depends(get_db), identity: IdentityContext = Depends(get_identity_context)):
    authorize(identity)
    rows = dict(db.execute(select(CommercialContract.status, func.count(CommercialContract.id)).where(
        CommercialContract.organization_id == identity.organization_id,
        CommercialContract.deleted_at.is_(None),
    ).group_by(CommercialContract.status)).all())
    overdue = db.scalar(select(func.count(CommercialContract.id)).where(CommercialContract.organization_id == identity.organization_id, CommercialContract.deleted_at.is_(None), CommercialContract.status == "ENVIADO", CommercialContract.signature_due_at < date.today())) or 0
    return ContractSummary(
        total=sum(rows.values()), draft=rows.get("RASCUNHO", 0),
        awaiting_approval=rows.get("EM_REVISAO", 0), awaiting_signature=rows.get("ENVIADO", 0),
        signed=rows.get("ASSINADO", 0), cancelled=rows.get("CANCELADO", 0), overdue_signatures=overdue,
    )


@router.get("", response_model=list[ContractListItem])
def list_contracts(
    search: str | None = Query(None, max_length=200), status: str | None = Query(None, max_length=20),
    limit: int = Query(100, ge=1, le=200), db: Session = Depends(get_db),
    identity: IdentityContext = Depends(get_identity_context),
):
    authorize(identity)
    conditions = [CommercialContract.organization_id == identity.organization_id, CommercialContract.deleted_at.is_(None)]
    if status: conditions.append(CommercialContract.status == status)
    if search:
        term = f"%{search.strip()}%"
        conditions.append(or_(CommercialContract.contract_number.ilike(term), CommercialContract.title.ilike(term), Client.full_name.ilike(term), Lead.full_name.ilike(term)))
    rows = db.execute(select(CommercialContract, Client.full_name, Lead.full_name).join(Client, Client.id == CommercialContract.client_id).join(Lead, Lead.id == CommercialContract.lead_id).where(*conditions).order_by(CommercialContract.updated_at.desc()).limit(limit)).all()
    return [ContractListItem(**ContractRead.model_validate(contract).model_dump(), client_name=client_name, lead_name=lead_name) for contract, client_name, lead_name in rows]
