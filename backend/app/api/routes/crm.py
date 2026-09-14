from __future__ import annotations

from datetime import date, datetime, time, timedelta, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy import func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.deps import require_permissions
from app.db.session import get_db
from app.models.case import Case
from app.models.client import Client
from app.models.crm import (
    CRMContact,
    CRMInteraction,
    CRMOpportunity,
    CRMOpportunityStageHistory,
    CRMTask,
)
from app.models.enums import ClientStatus
from app.models.user import User
from app.schemas.client import ClientRead
from app.schemas.crm import (
    CRMStage,
    CRMDashboard,
    CRMSummary,
    CaseRead,
    ContactCreate,
    ContactRead,
    ContactUpdate,
    InteractionCreate,
    InteractionRead,
    LeadDetail,
    OpportunityConvertRequest,
    OpportunityConvertResponse,
    OpportunityCreate,
    OpportunityRead,
    OpportunityStageChange,
    OpportunityStageHistoryRead,
    OpportunityUpdate,
    PipelineCard,
    PipelineColumn,
    TaskCreate,
    TaskPriority,
    TaskRead,
    TaskStatus,
    TaskUpdate,
)
from app.security.identity import IdentityContext
from app.security.permissions import PermissionCode
from app.services.audit import record_audit

router = APIRouter()

PIPELINE_STAGES: tuple[str, ...] = (
    "new",
    "contacted",
    "qualified",
    "proposal",
    "converted",
    "lost",
)
PIPELINE_LABELS = {
    "new": "NOVO",
    "contacted": "CONTATADO",
    "qualified": "QUALIFICADO",
    "proposal": "PROPOSTA",
    "converted": "CONVERTIDO",
    "lost": "PERDIDO",
}
ALLOWED_STAGE_TRANSITIONS: dict[str, set[str]] = {
    "new": {"contacted", "qualified", "proposal", "converted", "lost"},
    "contacted": {"qualified", "proposal", "converted", "lost"},
    "qualified": {"contacted", "proposal", "converted", "lost"},
    "proposal": {"qualified", "converted", "lost"},
    "converted": set(),
    "lost": {"new", "contacted", "qualified", "proposal"},
}


def _audit_value(value):
    if isinstance(value, UUID):
        return str(value)
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    return value


def _audit_dict(values: dict) -> dict:
    return {key: _audit_value(value) for key, value in values.items()}


def tenant_item(model, db: Session, ident: IdentityContext, item_id: UUID):
    obj = db.scalar(
        select(model).where(
            model.id == item_id,
            model.organization_id == ident.organization_id,
        )
    )
    if not obj:
        raise HTTPException(status_code=404, detail="Registro CRM não encontrado")
    return obj


def validate_client(db: Session, ident: IdentityContext, client_id: UUID | None) -> Client | None:
    if client_id is None:
        return None
    client = db.scalar(
        select(Client).where(
            Client.id == client_id,
            Client.organization_id == ident.organization_id,
        )
    )
    if not client:
        raise HTTPException(status_code=422, detail="Cliente não pertence à organização")
    return client


def validate_user(db: Session, ident: IdentityContext, user_id: UUID | None) -> User | None:
    if user_id is None:
        return None
    user = db.scalar(
        select(User).where(
            User.id == user_id,
            User.organization_id == ident.organization_id,
        )
    )
    if not user:
        raise HTTPException(status_code=422, detail="Usuário não pertence à organização")
    return user


def commit(db: Session, message: str = "Conflito ao salvar registro CRM") -> None:
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail=message) from exc


def _range_conditions(column, date_from: date | None, date_to: date | None):
    conditions = []
    if date_from:
        conditions.append(
            column >= datetime.combine(date_from, time.min, tzinfo=timezone.utc)
        )
    if date_to:
        conditions.append(
            column < datetime.combine(date_to + timedelta(days=1), time.min, tzinfo=timezone.utc)
        )
    return conditions


def _dimension_conditions(
    *,
    owner_id: UUID | None,
    source: str | None,
    service: str | None,
):
    conditions = []
    if owner_id:
        conditions.append(CRMOpportunity.owner_id == owner_id)
    if source:
        conditions.append(func.lower(CRMOpportunity.source) == source.strip().lower())
    if service:
        conditions.append(func.lower(CRMOpportunity.service) == service.strip().lower())
    return conditions


def _record_stage_history(
    db: Session,
    ident: IdentityContext,
    opportunity: CRMOpportunity,
    *,
    from_stage: str | None,
    to_stage: str,
    note: str | None = None,
) -> None:
    db.add(
        CRMOpportunityStageHistory(
            organization_id=ident.organization_id,
            opportunity_id=opportunity.id,
            changed_by_id=ident.user_id,
            from_stage=from_stage,
            to_stage=to_stage,
            note=note,
            changed_at=datetime.now(timezone.utc),
        )
    )


def _move_stage(
    db: Session,
    ident: IdentityContext,
    opportunity: CRMOpportunity,
    *,
    new_stage: str,
    note: str | None = None,
    lost_reason: str | None = None,
) -> None:
    old_stage = opportunity.stage
    if new_stage == old_stage:
        return
    allowed = ALLOWED_STAGE_TRANSITIONS.get(old_stage, set())
    if new_stage not in allowed:
        raise HTTPException(
            status_code=422,
            detail=f"Transição de etapa inválida: {old_stage} -> {new_stage}",
        )

    now = datetime.now(timezone.utc)
    opportunity.stage = new_stage
    opportunity.stage_changed_at = now

    if new_stage == "converted":
        opportunity.converted_at = now
        opportunity.lost_at = None
        opportunity.lost_reason = None
    elif new_stage == "lost":
        opportunity.lost_at = now
        opportunity.converted_at = None
        if lost_reason is not None:
            opportunity.lost_reason = lost_reason
    else:
        if old_stage == "lost":
            opportunity.lost_at = None
            opportunity.lost_reason = None
        if old_stage == "converted":
            opportunity.converted_at = None

    _record_stage_history(
        db,
        ident,
        opportunity,
        from_stage=old_stage,
        to_stage=new_stage,
        note=note,
    )
    record_audit(
        db,
        organization_id=ident.organization_id,
        user_id=ident.user_id,
        entity_type="crm_opportunity",
        entity_id=opportunity.id,
        action="stage_change",
        old_values={"stage": old_stage},
        new_values={"stage": new_stage, "note": note, "lost_reason": lost_reason},
    )


@router.get("/contacts", response_model=list[ContactRead])
def list_contacts(
    search: str | None = Query(None, min_length=2, max_length=200),
    client_id: UUID | None = None,
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    ident: IdentityContext = Depends(require_permissions(PermissionCode.CRM_READ.value)),
):
    query = select(CRMContact).where(CRMContact.organization_id == ident.organization_id)
    if search:
        term = f"%{search.strip()}%"
        query = query.where(
            or_(
                CRMContact.name.ilike(term),
                CRMContact.email.ilike(term),
                CRMContact.phone.ilike(term),
            )
        )
    if client_id:
        query = query.where(CRMContact.client_id == client_id)
    return list(
        db.scalars(
            query.order_by(CRMContact.name, CRMContact.id).offset(offset).limit(limit)
        )
    )


@router.post("/contacts", response_model=ContactRead, status_code=status.HTTP_201_CREATED)
def create_contact(
    payload: ContactCreate,
    db: Session = Depends(get_db),
    ident: IdentityContext = Depends(require_permissions(PermissionCode.CRM_CREATE.value)),
):
    validate_client(db, ident, payload.client_id)
    obj = CRMContact(organization_id=ident.organization_id, **payload.model_dump())
    db.add(obj)
    db.flush()
    record_audit(
        db,
        organization_id=ident.organization_id,
        user_id=ident.user_id,
        entity_type="crm_contact",
        entity_id=obj.id,
        action="create",
        new_values={"name": obj.name, "client_id": str(obj.client_id) if obj.client_id else None},
    )
    commit(db)
    db.refresh(obj)
    return obj


@router.get("/contacts/{item_id}", response_model=ContactRead)
def get_contact(
    item_id: UUID,
    db: Session = Depends(get_db),
    ident: IdentityContext = Depends(require_permissions(PermissionCode.CRM_READ.value)),
):
    return tenant_item(CRMContact, db, ident, item_id)


@router.patch("/contacts/{item_id}", response_model=ContactRead)
def update_contact(
    item_id: UUID,
    payload: ContactUpdate,
    db: Session = Depends(get_db),
    ident: IdentityContext = Depends(require_permissions(PermissionCode.CRM_UPDATE.value)),
):
    obj = tenant_item(CRMContact, db, ident, item_id)
    changes = payload.model_dump(exclude_unset=True)
    if "client_id" in changes:
        validate_client(db, ident, changes["client_id"])
    old_values = {key: getattr(obj, key) for key in changes}
    for key, value in changes.items():
        setattr(obj, key, value)
    record_audit(
        db,
        organization_id=ident.organization_id,
        user_id=ident.user_id,
        entity_type="crm_contact",
        entity_id=obj.id,
        action="update",
        old_values=_audit_dict(old_values),
        new_values=_audit_dict(changes),
    )
    commit(db)
    db.refresh(obj)
    return obj


@router.delete("/contacts/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_contact(
    item_id: UUID,
    db: Session = Depends(get_db),
    ident: IdentityContext = Depends(require_permissions(PermissionCode.CRM_DELETE.value)),
):
    obj = tenant_item(CRMContact, db, ident, item_id)
    record_audit(
        db,
        organization_id=ident.organization_id,
        user_id=ident.user_id,
        entity_type="crm_contact",
        entity_id=obj.id,
        action="delete",
        old_values={"name": obj.name},
    )
    db.delete(obj)
    commit(db)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/interactions", response_model=list[InteractionRead])
def list_interactions(
    client_id: UUID | None = None,
    opportunity_id: UUID | None = None,
    interaction_type: str | None = None,
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    ident: IdentityContext = Depends(require_permissions(PermissionCode.CRM_READ.value)),
):
    query = select(CRMInteraction).where(
        CRMInteraction.organization_id == ident.organization_id
    )
    if client_id:
        query = query.where(CRMInteraction.client_id == client_id)
    if opportunity_id:
        query = query.where(CRMInteraction.opportunity_id == opportunity_id)
    if interaction_type:
        query = query.where(CRMInteraction.interaction_type == interaction_type)
    return list(
        db.scalars(
            query.order_by(CRMInteraction.occurred_at.desc(), CRMInteraction.id)
            .offset(offset)
            .limit(limit)
        )
    )


@router.post("/interactions", response_model=InteractionRead, status_code=status.HTTP_201_CREATED)
def create_interaction(
    payload: InteractionCreate,
    db: Session = Depends(get_db),
    ident: IdentityContext = Depends(require_permissions(PermissionCode.CRM_CREATE.value)),
):
    validate_client(db, ident, payload.client_id)
    if payload.opportunity_id:
        opportunity = tenant_item(CRMOpportunity, db, ident, payload.opportunity_id)
        if opportunity.client_id != payload.client_id:
            raise HTTPException(
                status_code=422,
                detail="A oportunidade não pertence ao cliente informado",
            )
    obj = CRMInteraction(
        organization_id=ident.organization_id,
        user_id=ident.user_id,
        **payload.model_dump(),
    )
    db.add(obj)
    db.flush()
    record_audit(
        db,
        organization_id=ident.organization_id,
        user_id=ident.user_id,
        entity_type="crm_interaction",
        entity_id=obj.id,
        action="create",
        new_values={"subject": obj.subject, "interaction_type": obj.interaction_type},
    )
    commit(db)
    db.refresh(obj)
    return obj


@router.get("/interactions/{item_id}", response_model=InteractionRead)
def get_interaction(
    item_id: UUID,
    db: Session = Depends(get_db),
    ident: IdentityContext = Depends(require_permissions(PermissionCode.CRM_READ.value)),
):
    return tenant_item(CRMInteraction, db, ident, item_id)


@router.delete("/interactions/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_interaction(
    item_id: UUID,
    db: Session = Depends(get_db),
    ident: IdentityContext = Depends(require_permissions(PermissionCode.CRM_DELETE.value)),
):
    obj = tenant_item(CRMInteraction, db, ident, item_id)
    record_audit(
        db,
        organization_id=ident.organization_id,
        user_id=ident.user_id,
        entity_type="crm_interaction",
        entity_id=obj.id,
        action="delete",
        old_values={"subject": obj.subject, "interaction_type": obj.interaction_type},
    )
    db.delete(obj)
    commit(db)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/opportunities", response_model=list[OpportunityRead])
def list_opportunities(
    stage: CRMStage | None = None,
    client_id: UUID | None = None,
    owner_id: UUID | None = None,
    source: str | None = None,
    service: str | None = None,
    search: str | None = Query(None, min_length=2, max_length=200),
    created_from: date | None = None,
    created_to: date | None = None,
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    ident: IdentityContext = Depends(require_permissions(PermissionCode.CRM_READ.value)),
):
    query = select(CRMOpportunity).where(
        CRMOpportunity.organization_id == ident.organization_id
    )
    if stage:
        query = query.where(CRMOpportunity.stage == stage)
    if client_id:
        query = query.where(CRMOpportunity.client_id == client_id)
    for condition in _dimension_conditions(owner_id=owner_id, source=source, service=service):
        query = query.where(condition)
    for condition in _range_conditions(CRMOpportunity.created_at, created_from, created_to):
        query = query.where(condition)
    if search:
        query = query.join(Client, Client.id == CRMOpportunity.client_id).where(
            or_(
                CRMOpportunity.title.ilike(f"%{search.strip()}%"),
                Client.full_name.ilike(f"%{search.strip()}%"),
                Client.phone.ilike(f"%{search.strip()}%"),
            )
        )
    return list(
        db.scalars(
            query.order_by(CRMOpportunity.updated_at.desc(), CRMOpportunity.id)
            .offset(offset)
            .limit(limit)
        )
    )


@router.post("/opportunities", response_model=OpportunityRead, status_code=status.HTTP_201_CREATED)
def create_opportunity(
    payload: OpportunityCreate,
    db: Session = Depends(get_db),
    ident: IdentityContext = Depends(require_permissions(PermissionCode.CRM_CREATE.value)),
):
    validate_client(db, ident, payload.client_id)
    validate_user(db, ident, payload.owner_id)
    data = payload.model_dump()
    now = datetime.now(timezone.utc)
    if data["stage"] == "converted":
        data["converted_at"] = now
    elif data["stage"] == "lost":
        data["lost_at"] = now
    obj = CRMOpportunity(organization_id=ident.organization_id, **data)
    db.add(obj)
    db.flush()
    _record_stage_history(
        db,
        ident,
        obj,
        from_stage=None,
        to_stage=obj.stage,
        note="Criação da oportunidade",
    )
    record_audit(
        db,
        organization_id=ident.organization_id,
        user_id=ident.user_id,
        entity_type="crm_opportunity",
        entity_id=obj.id,
        action="create",
        new_values={
            "title": obj.title,
            "stage": obj.stage,
            "source": obj.source,
            "service": obj.service,
            "client_id": str(obj.client_id),
        },
    )
    commit(db)
    db.refresh(obj)
    return obj


@router.get("/opportunities/{item_id}", response_model=OpportunityRead)
def get_opportunity(
    item_id: UUID,
    db: Session = Depends(get_db),
    ident: IdentityContext = Depends(require_permissions(PermissionCode.CRM_READ.value)),
):
    return tenant_item(CRMOpportunity, db, ident, item_id)


@router.patch("/opportunities/{item_id}", response_model=OpportunityRead)
def update_opportunity(
    item_id: UUID,
    payload: OpportunityUpdate,
    db: Session = Depends(get_db),
    ident: IdentityContext = Depends(require_permissions(PermissionCode.CRM_UPDATE.value)),
):
    obj = tenant_item(CRMOpportunity, db, ident, item_id)
    changes = payload.model_dump(exclude_unset=True)
    if "client_id" in changes:
        validate_client(db, ident, changes["client_id"])
    if "owner_id" in changes:
        validate_user(db, ident, changes["owner_id"])

    stage = changes.pop("stage", None)
    lost_reason = changes.get("lost_reason")
    old_values = {key: getattr(obj, key) for key in changes}
    for key, value in changes.items():
        setattr(obj, key, value)

    if changes:
        record_audit(
            db,
            organization_id=ident.organization_id,
            user_id=ident.user_id,
            entity_type="crm_opportunity",
            entity_id=obj.id,
            action="update",
            old_values=_audit_dict(old_values),
            new_values=_audit_dict(changes),
        )
    if stage:
        _move_stage(
            db,
            ident,
            obj,
            new_stage=stage,
            lost_reason=lost_reason,
        )
    commit(db)
    db.refresh(obj)
    return obj


@router.post("/opportunities/{item_id}/stage", response_model=OpportunityRead)
def change_opportunity_stage(
    item_id: UUID,
    payload: OpportunityStageChange,
    db: Session = Depends(get_db),
    ident: IdentityContext = Depends(require_permissions(PermissionCode.CRM_UPDATE.value)),
):
    obj = tenant_item(CRMOpportunity, db, ident, item_id)
    _move_stage(
        db,
        ident,
        obj,
        new_stage=payload.stage,
        note=payload.note,
        lost_reason=payload.lost_reason,
    )
    commit(db)
    db.refresh(obj)
    return obj


@router.get(
    "/opportunities/{item_id}/history",
    response_model=list[OpportunityStageHistoryRead],
)
def opportunity_history(
    item_id: UUID,
    db: Session = Depends(get_db),
    ident: IdentityContext = Depends(require_permissions(PermissionCode.CRM_READ.value)),
):
    tenant_item(CRMOpportunity, db, ident, item_id)
    stmt = (
        select(CRMOpportunityStageHistory)
        .where(
            CRMOpportunityStageHistory.organization_id == ident.organization_id,
            CRMOpportunityStageHistory.opportunity_id == item_id,
        )
        .order_by(CRMOpportunityStageHistory.changed_at, CRMOpportunityStageHistory.id)
    )
    return list(db.scalars(stmt))


@router.post(
    "/opportunities/{item_id}/convert",
    response_model=OpportunityConvertResponse,
)
def convert_opportunity(
    item_id: UUID,
    payload: OpportunityConvertRequest,
    db: Session = Depends(get_db),
    ident: IdentityContext = Depends(require_permissions(PermissionCode.CRM_CONVERT.value)),
):
    opportunity = tenant_item(CRMOpportunity, db, ident, item_id)
    client = validate_client(db, ident, opportunity.client_id)
    assert client is not None

    if opportunity.stage != "converted":
        _move_stage(
            db,
            ident,
            opportunity,
            new_stage="converted",
            note=payload.note or "Lead convertido em cliente",
        )

    if client.status != ClientStatus.CONTRACTED.value:
        previous_status = client.status
        client.status = ClientStatus.CONTRACTED.value
        record_audit(
            db,
            organization_id=ident.organization_id,
            user_id=ident.user_id,
            entity_type="client",
            entity_id=client.id,
            action="crm_convert",
            old_values={"status": previous_status},
            new_values={"status": client.status},
        )

    case = db.scalar(
        select(Case).where(
            Case.organization_id == ident.organization_id,
            Case.opportunity_id == opportunity.id,
        )
    )
    is_cs_recupera = "recupera" in (opportunity.service or "").casefold()
    if payload.create_case and is_cs_recupera and case is None:
        case = Case(
            organization_id=ident.organization_id,
            client_id=client.id,
            opportunity_id=opportunity.id,
            assigned_user_id=opportunity.owner_id,
            service=opportunity.service or "CS Recupera",
            title=payload.case_title or f"CS Recupera — {client.full_name}",
            status=payload.case_status,
        )
        db.add(case)
        db.flush()
        record_audit(
            db,
            organization_id=ident.organization_id,
            user_id=ident.user_id,
            entity_type="case",
            entity_id=case.id,
            action="create",
            new_values={
                "client_id": str(client.id),
                "opportunity_id": str(opportunity.id),
                "service": case.service,
                "status": case.status,
            },
        )

    commit(db)
    db.refresh(opportunity)
    db.refresh(client)
    if case is not None:
        db.refresh(case)

    return OpportunityConvertResponse(
        opportunity=OpportunityRead.model_validate(opportunity),
        client=ClientRead.model_validate(client),
        case=CaseRead.model_validate(case) if case else None,
    )


@router.get("/opportunities/{item_id}/detail", response_model=LeadDetail)
def opportunity_detail(
    item_id: UUID,
    db: Session = Depends(get_db),
    ident: IdentityContext = Depends(require_permissions(PermissionCode.CRM_READ.value)),
):
    opportunity = tenant_item(CRMOpportunity, db, ident, item_id)
    client = validate_client(db, ident, opportunity.client_id)
    assert client is not None

    interactions = list(
        db.scalars(
            select(CRMInteraction)
            .where(
                CRMInteraction.organization_id == ident.organization_id,
                CRMInteraction.client_id == client.id,
                or_(
                    CRMInteraction.opportunity_id == opportunity.id,
                    CRMInteraction.opportunity_id.is_(None),
                ),
            )
            .order_by(CRMInteraction.occurred_at.desc(), CRMInteraction.id)
        )
    )
    tasks = list(
        db.scalars(
            select(CRMTask)
            .where(
                CRMTask.organization_id == ident.organization_id,
                CRMTask.opportunity_id == opportunity.id,
            )
            .order_by(CRMTask.due_at.asc().nullslast(), CRMTask.id)
        )
    )
    history = list(
        db.scalars(
            select(CRMOpportunityStageHistory)
            .where(
                CRMOpportunityStageHistory.organization_id == ident.organization_id,
                CRMOpportunityStageHistory.opportunity_id == opportunity.id,
            )
            .order_by(CRMOpportunityStageHistory.changed_at, CRMOpportunityStageHistory.id)
        )
    )
    case = db.scalar(
        select(Case).where(
            Case.organization_id == ident.organization_id,
            Case.opportunity_id == opportunity.id,
        )
    )
    return LeadDetail(
        opportunity=OpportunityRead.model_validate(opportunity),
        client=ClientRead.model_validate(client),
        interactions=[InteractionRead.model_validate(item) for item in interactions],
        tasks=[TaskRead.model_validate(item) for item in tasks],
        history=[OpportunityStageHistoryRead.model_validate(item) for item in history],
        case=CaseRead.model_validate(case) if case else None,
    )


@router.delete("/opportunities/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_opportunity(
    item_id: UUID,
    db: Session = Depends(get_db),
    ident: IdentityContext = Depends(require_permissions(PermissionCode.CRM_DELETE.value)),
):
    obj = tenant_item(CRMOpportunity, db, ident, item_id)
    record_audit(
        db,
        organization_id=ident.organization_id,
        user_id=ident.user_id,
        entity_type="crm_opportunity",
        entity_id=obj.id,
        action="delete",
        old_values={"title": obj.title, "stage": obj.stage},
    )
    db.delete(obj)
    commit(db)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/pipeline", response_model=list[PipelineColumn])
def pipeline(
    owner_id: UUID | None = None,
    source: str | None = None,
    service: str | None = None,
    search: str | None = Query(None, min_length=2, max_length=200),
    limit_per_stage: int = Query(100, ge=1, le=200),
    db: Session = Depends(get_db),
    ident: IdentityContext = Depends(require_permissions(PermissionCode.CRM_READ.value)),
):
    stmt = (
        select(
            CRMOpportunity,
            Client.full_name,
            Client.phone,
            User.full_name.label("owner_name"),
        )
        .join(Client, Client.id == CRMOpportunity.client_id)
        .outerjoin(User, User.id == CRMOpportunity.owner_id)
        .where(CRMOpportunity.organization_id == ident.organization_id)
    )
    for condition in _dimension_conditions(owner_id=owner_id, source=source, service=service):
        stmt = stmt.where(condition)
    if search:
        term = f"%{search.strip()}%"
        stmt = stmt.where(
            or_(
                CRMOpportunity.title.ilike(term),
                Client.full_name.ilike(term),
                Client.phone.ilike(term),
            )
        )
    rows = db.execute(
        stmt.order_by(
            CRMOpportunity.stage,
            CRMOpportunity.next_contact_at.asc().nullslast(),
            CRMOpportunity.updated_at.desc(),
        )
    ).all()

    grouped: dict[str, list[PipelineCard]] = {stage: [] for stage in PIPELINE_STAGES}
    for opportunity, client_name, phone, owner_name in rows:
        if opportunity.stage not in grouped:
            continue
        if len(grouped[opportunity.stage]) >= limit_per_stage:
            continue
        grouped[opportunity.stage].append(
            PipelineCard(
                opportunity_id=opportunity.id,
                client_id=opportunity.client_id,
                client_name=client_name,
                phone=phone,
                title=opportunity.title,
                stage=opportunity.stage,
                source=opportunity.source,
                service=opportunity.service,
                owner_id=opportunity.owner_id,
                owner_name=owner_name,
                next_contact_at=opportunity.next_contact_at,
                estimated_value=float(opportunity.estimated_value or 0),
                probability=opportunity.probability,
                updated_at=opportunity.updated_at,
            )
        )

    return [
        PipelineColumn(
            stage=stage,
            label=PIPELINE_LABELS[stage],
            count=len(grouped[stage]),
            items=grouped[stage],
        )
        for stage in PIPELINE_STAGES
    ]


@router.get("/tasks", response_model=list[TaskRead])
def list_tasks(
    task_status: TaskStatus | None = Query(None, alias="status"),
    priority: TaskPriority | None = None,
    assigned_to_id: UUID | None = None,
    opportunity_id: UUID | None = None,
    overdue_only: bool = False,
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    ident: IdentityContext = Depends(require_permissions(PermissionCode.CRM_READ.value)),
):
    query = select(CRMTask).where(CRMTask.organization_id == ident.organization_id)
    if task_status:
        query = query.where(CRMTask.status == task_status)
    if priority:
        query = query.where(CRMTask.priority == priority)
    if assigned_to_id:
        query = query.where(CRMTask.assigned_to_id == assigned_to_id)
    if opportunity_id:
        query = query.where(CRMTask.opportunity_id == opportunity_id)
    if overdue_only:
        query = query.where(
            CRMTask.status.notin_(["completed", "cancelled"]),
            CRMTask.due_at < datetime.now(timezone.utc),
        )
    return list(
        db.scalars(
            query.order_by(CRMTask.due_at.asc().nullslast(), CRMTask.id)
            .offset(offset)
            .limit(limit)
        )
    )


@router.post("/tasks", response_model=TaskRead, status_code=status.HTTP_201_CREATED)
def create_task(
    payload: TaskCreate,
    db: Session = Depends(get_db),
    ident: IdentityContext = Depends(require_permissions(PermissionCode.CRM_CREATE.value)),
):
    data = payload.model_dump()
    opportunity = None
    if payload.opportunity_id:
        opportunity = tenant_item(CRMOpportunity, db, ident, payload.opportunity_id)
        if data["client_id"] is None:
            data["client_id"] = opportunity.client_id
        elif data["client_id"] != opportunity.client_id:
            raise HTTPException(
                status_code=422,
                detail="A oportunidade não pertence ao cliente informado",
            )
    validate_client(db, ident, data["client_id"])
    validate_user(db, ident, payload.assigned_to_id)
    obj = CRMTask(organization_id=ident.organization_id, **data)
    if obj.status == "completed":
        obj.completed_at = datetime.now(timezone.utc)
    db.add(obj)
    db.flush()
    record_audit(
        db,
        organization_id=ident.organization_id,
        user_id=ident.user_id,
        entity_type="crm_task",
        entity_id=obj.id,
        action="create",
        new_values={"title": obj.title, "status": obj.status, "priority": obj.priority},
    )
    commit(db)
    db.refresh(obj)
    return obj


@router.get("/tasks/{item_id}", response_model=TaskRead)
def get_task(
    item_id: UUID,
    db: Session = Depends(get_db),
    ident: IdentityContext = Depends(require_permissions(PermissionCode.CRM_READ.value)),
):
    return tenant_item(CRMTask, db, ident, item_id)


@router.patch("/tasks/{item_id}", response_model=TaskRead)
def update_task(
    item_id: UUID,
    payload: TaskUpdate,
    db: Session = Depends(get_db),
    ident: IdentityContext = Depends(require_permissions(PermissionCode.CRM_UPDATE.value)),
):
    obj = tenant_item(CRMTask, db, ident, item_id)
    changes = payload.model_dump(exclude_unset=True)
    if "client_id" in changes:
        validate_client(db, ident, changes["client_id"])
    if "assigned_to_id" in changes:
        validate_user(db, ident, changes["assigned_to_id"])
    if changes.get("opportunity_id"):
        opportunity = tenant_item(CRMOpportunity, db, ident, changes["opportunity_id"])
        effective_client_id = changes.get("client_id", obj.client_id)
        if effective_client_id and opportunity.client_id != effective_client_id:
            raise HTTPException(
                status_code=422,
                detail="A oportunidade não pertence ao cliente informado",
            )
    old_values = {key: getattr(obj, key) for key in changes}
    for key, value in changes.items():
        setattr(obj, key, value)
    if "status" in changes:
        obj.completed_at = (
            datetime.now(timezone.utc) if changes["status"] == "completed" else None
        )
    record_audit(
        db,
        organization_id=ident.organization_id,
        user_id=ident.user_id,
        entity_type="crm_task",
        entity_id=obj.id,
        action="update",
        old_values=_audit_dict(old_values),
        new_values=_audit_dict(changes),
    )
    commit(db)
    db.refresh(obj)
    return obj


@router.post("/tasks/{item_id}/complete", response_model=TaskRead)
def complete_task(
    item_id: UUID,
    db: Session = Depends(get_db),
    ident: IdentityContext = Depends(require_permissions(PermissionCode.CRM_UPDATE.value)),
):
    obj = tenant_item(CRMTask, db, ident, item_id)
    old_status = obj.status
    obj.status = "completed"
    obj.completed_at = datetime.now(timezone.utc)
    record_audit(
        db,
        organization_id=ident.organization_id,
        user_id=ident.user_id,
        entity_type="crm_task",
        entity_id=obj.id,
        action="complete",
        old_values={"status": old_status},
        new_values={"status": "completed"},
    )
    commit(db)
    db.refresh(obj)
    return obj


@router.delete("/tasks/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task(
    item_id: UUID,
    db: Session = Depends(get_db),
    ident: IdentityContext = Depends(require_permissions(PermissionCode.CRM_DELETE.value)),
):
    obj = tenant_item(CRMTask, db, ident, item_id)
    record_audit(
        db,
        organization_id=ident.organization_id,
        user_id=ident.user_id,
        entity_type="crm_task",
        entity_id=obj.id,
        action="delete",
        old_values={"title": obj.title, "status": obj.status},
    )
    db.delete(obj)
    commit(db)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/summary", response_model=CRMSummary)
def summary(
    db: Session = Depends(get_db),
    ident: IdentityContext = Depends(require_permissions(PermissionCode.CRM_READ.value)),
):
    org = ident.organization_id

    def count(model):
        return (
            db.scalar(
                select(func.count()).select_from(model).where(model.organization_id == org)
            )
            or 0
        )

    open_filter = CRMOpportunity.stage.notin_(["converted", "lost"])
    value = (
        db.scalar(
            select(func.coalesce(func.sum(CRMOpportunity.estimated_value), 0)).where(
                CRMOpportunity.organization_id == org,
                open_filter,
            )
        )
        or 0
    )
    weighted = (
        db.scalar(
            select(
                func.coalesce(
                    func.sum(
                        CRMOpportunity.estimated_value
                        * CRMOpportunity.probability
                        / 100.0
                    ),
                    0,
                )
            ).where(
                CRMOpportunity.organization_id == org,
                open_filter,
            )
        )
        or 0
    )
    pending = (
        db.scalar(
            select(func.count())
            .select_from(CRMTask)
            .where(
                CRMTask.organization_id == org,
                CRMTask.status.notin_(["completed", "cancelled"]),
            )
        )
        or 0
    )
    overdue = (
        db.scalar(
            select(func.count())
            .select_from(CRMTask)
            .where(
                CRMTask.organization_id == org,
                CRMTask.status.notin_(["completed", "cancelled"]),
                CRMTask.due_at < datetime.now(timezone.utc),
            )
        )
        or 0
    )
    return CRMSummary(
        contacts=count(CRMContact),
        interactions=count(CRMInteraction),
        opportunities=count(CRMOpportunity),
        open_pipeline_value=float(value),
        weighted_pipeline_value=float(weighted),
        pending_tasks=pending,
        overdue_tasks=overdue,
    )


@router.get("/dashboard", response_model=CRMDashboard)
def crm_dashboard(
    date_from: date | None = None,
    date_to: date | None = None,
    owner_id: UUID | None = None,
    source: str | None = None,
    service: str | None = None,
    db: Session = Depends(get_db),
    ident: IdentityContext = Depends(require_permissions(PermissionCode.CRM_READ.value)),
):
    org_condition = CRMOpportunity.organization_id == ident.organization_id
    dimensions = _dimension_conditions(owner_id=owner_id, source=source, service=service)

    def opportunity_count(*conditions):
        stmt = select(func.count()).select_from(CRMOpportunity).where(org_condition)
        for condition in dimensions:
            stmt = stmt.where(condition)
        for condition in conditions:
            stmt = stmt.where(condition)
        return db.scalar(stmt) or 0

    created_range = _range_conditions(CRMOpportunity.created_at, date_from, date_to)
    converted_range = _range_conditions(CRMOpportunity.converted_at, date_from, date_to)
    lost_range = _range_conditions(CRMOpportunity.lost_at, date_from, date_to)

    leads_new = opportunity_count(*created_range)
    leads_in_progress = opportunity_count(
        CRMOpportunity.stage.in_(["contacted", "qualified", "proposal"]),
        *created_range,
    )
    leads_qualified = opportunity_count(
        CRMOpportunity.stage == "qualified",
        *created_range,
    )
    open_proposals = opportunity_count(
        CRMOpportunity.stage == "proposal",
        *created_range,
    )
    leads_converted = opportunity_count(
        CRMOpportunity.stage == "converted",
        *converted_range,
    )
    leads_lost = opportunity_count(
        CRMOpportunity.stage == "lost",
        *lost_range,
    )

    closed = leads_converted + leads_lost
    conversion_rate = round((leads_converted / closed * 100.0), 2) if closed else 0.0

    converted_stmt = select(CRMOpportunity).where(
        org_condition,
        CRMOpportunity.stage == "converted",
    )
    for condition in dimensions:
        converted_stmt = converted_stmt.where(condition)
    for condition in converted_range:
        converted_stmt = converted_stmt.where(condition)
    converted_items = list(db.scalars(converted_stmt))
    durations = [
        (item.converted_at - item.created_at).total_seconds() / 86400.0
        for item in converted_items
        if item.converted_at and item.created_at
    ]
    avg_days = round(sum(durations) / len(durations), 2) if durations else None

    proposal_stmt = select(
        func.coalesce(func.sum(CRMOpportunity.estimated_value), 0)
    ).where(
        org_condition,
        CRMOpportunity.stage == "proposal",
    )
    for condition in dimensions:
        proposal_stmt = proposal_stmt.where(condition)
    for condition in created_range:
        proposal_stmt = proposal_stmt.where(condition)
    estimated_proposal_revenue = float(db.scalar(proposal_stmt) or 0)

    contracted_stmt = select(
        func.coalesce(func.sum(CRMOpportunity.estimated_value), 0)
    ).where(
        org_condition,
        CRMOpportunity.stage == "converted",
    )
    for condition in dimensions:
        contracted_stmt = contracted_stmt.where(condition)
    for condition in converted_range:
        contracted_stmt = contracted_stmt.where(condition)
    contracted_revenue = float(db.scalar(contracted_stmt) or 0)

    overdue_stmt = (
        select(func.count())
        .select_from(CRMTask)
        .join(CRMOpportunity, CRMOpportunity.id == CRMTask.opportunity_id)
        .where(
            CRMTask.organization_id == ident.organization_id,
            CRMTask.status.notin_(["completed", "cancelled"]),
            CRMTask.due_at < datetime.now(timezone.utc),
            org_condition,
        )
    )
    for condition in dimensions:
        overdue_stmt = overdue_stmt.where(condition)
    overdue_followups = db.scalar(overdue_stmt) or 0

    return CRMDashboard(
        leads_new=leads_new,
        leads_in_progress=leads_in_progress,
        leads_qualified=leads_qualified,
        open_proposals=open_proposals,
        leads_converted=leads_converted,
        leads_lost=leads_lost,
        conversion_rate=conversion_rate,
        avg_days_to_conversion=avg_days,
        estimated_proposal_revenue=estimated_proposal_revenue,
        contracted_revenue=contracted_revenue,
        overdue_followups=overdue_followups,
    )
