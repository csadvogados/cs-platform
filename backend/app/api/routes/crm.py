from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy import func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.deps import get_identity_context
from app.db.session import get_db
from app.models.client import Client
from app.models.crm import CRMContact, CRMInteraction, CRMOpportunity, CRMTask
from app.models.user import User
from app.schemas.crm import (
    CRMStage,
    CRMSummary,
    ContactCreate,
    ContactRead,
    ContactUpdate,
    InteractionCreate,
    InteractionRead,
    OpportunityCreate,
    OpportunityRead,
    OpportunityUpdate,
    TaskCreate,
    TaskPriority,
    TaskRead,
    TaskStatus,
    TaskUpdate,
)
from app.security.identity import IdentityContext
from app.services.audit import record_audit

router = APIRouter()


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


def validate_client(db: Session, ident: IdentityContext, client_id: UUID | None) -> None:
    if client_id is None:
        return
    exists = db.scalar(
        select(Client.id).where(
            Client.id == client_id,
            Client.organization_id == ident.organization_id,
        )
    )
    if not exists:
        raise HTTPException(status_code=422, detail="Cliente não pertence à organização")


def validate_user(db: Session, ident: IdentityContext, user_id: UUID | None) -> None:
    if user_id is None:
        return
    exists = db.scalar(
        select(User.id).where(
            User.id == user_id,
            User.organization_id == ident.organization_id,
        )
    )
    if not exists:
        raise HTTPException(status_code=422, detail="Usuário não pertence à organização")


def commit(db: Session, message: str = "Conflito ao salvar registro CRM") -> None:
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail=message) from exc


@router.get("/contacts", response_model=list[ContactRead])
def list_contacts(
    search: str | None = Query(None, min_length=2, max_length=200),
    client_id: UUID | None = None,
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    ident: IdentityContext = Depends(get_identity_context),
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
    return list(db.scalars(query.order_by(CRMContact.name, CRMContact.id).offset(offset).limit(limit)))


@router.post("/contacts", response_model=ContactRead, status_code=status.HTTP_201_CREATED)
def create_contact(payload: ContactCreate, db: Session = Depends(get_db), ident: IdentityContext = Depends(get_identity_context)):
    validate_client(db, ident, payload.client_id)
    obj = CRMContact(organization_id=ident.organization_id, **payload.model_dump())
    db.add(obj)
    commit(db)
    db.refresh(obj)
    record_audit(db, organization_id=ident.organization_id, user_id=ident.user_id, entity_type="crm_contact", entity_id=obj.id, action="create", new_values={"name": obj.name})
    db.commit()
    return obj


@router.get("/contacts/{item_id}", response_model=ContactRead)
def get_contact(item_id: UUID, db: Session = Depends(get_db), ident: IdentityContext = Depends(get_identity_context)):
    return tenant_item(CRMContact, db, ident, item_id)


@router.patch("/contacts/{item_id}", response_model=ContactRead)
def update_contact(item_id: UUID, payload: ContactUpdate, db: Session = Depends(get_db), ident: IdentityContext = Depends(get_identity_context)):
    obj = tenant_item(CRMContact, db, ident, item_id)
    changes = payload.model_dump(exclude_unset=True)
    if "client_id" in changes:
        validate_client(db, ident, changes["client_id"])
    for key, value in changes.items():
        setattr(obj, key, value)
    commit(db)
    db.refresh(obj)
    return obj


@router.delete("/contacts/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_contact(item_id: UUID, db: Session = Depends(get_db), ident: IdentityContext = Depends(get_identity_context)):
    obj = tenant_item(CRMContact, db, ident, item_id)
    db.delete(obj)
    commit(db)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/interactions", response_model=list[InteractionRead])
def list_interactions(
    client_id: UUID | None = None,
    interaction_type: str | None = None,
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    ident: IdentityContext = Depends(get_identity_context),
):
    query = select(CRMInteraction).where(CRMInteraction.organization_id == ident.organization_id)
    if client_id:
        query = query.where(CRMInteraction.client_id == client_id)
    if interaction_type:
        query = query.where(CRMInteraction.interaction_type == interaction_type)
    return list(db.scalars(query.order_by(CRMInteraction.occurred_at.desc(), CRMInteraction.id).offset(offset).limit(limit)))


@router.post("/interactions", response_model=InteractionRead, status_code=status.HTTP_201_CREATED)
def create_interaction(payload: InteractionCreate, db: Session = Depends(get_db), ident: IdentityContext = Depends(get_identity_context)):
    validate_client(db, ident, payload.client_id)
    obj = CRMInteraction(organization_id=ident.organization_id, user_id=ident.user_id, **payload.model_dump())
    db.add(obj)
    commit(db)
    db.refresh(obj)
    return obj


@router.delete("/interactions/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_interaction(item_id: UUID, db: Session = Depends(get_db), ident: IdentityContext = Depends(get_identity_context)):
    db.delete(tenant_item(CRMInteraction, db, ident, item_id))
    commit(db)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/opportunities", response_model=list[OpportunityRead])
def list_opportunities(
    stage: CRMStage | None = None,
    client_id: UUID | None = None,
    owner_id: UUID | None = None,
    search: str | None = Query(None, min_length=2, max_length=200),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    ident: IdentityContext = Depends(get_identity_context),
):
    query = select(CRMOpportunity).where(CRMOpportunity.organization_id == ident.organization_id)
    if stage:
        query = query.where(CRMOpportunity.stage == stage)
    if client_id:
        query = query.where(CRMOpportunity.client_id == client_id)
    if owner_id:
        query = query.where(CRMOpportunity.owner_id == owner_id)
    if search:
        query = query.where(CRMOpportunity.title.ilike(f"%{search.strip()}%"))
    return list(db.scalars(query.order_by(CRMOpportunity.updated_at.desc(), CRMOpportunity.id).offset(offset).limit(limit)))


@router.post("/opportunities", response_model=OpportunityRead, status_code=status.HTTP_201_CREATED)
def create_opportunity(payload: OpportunityCreate, db: Session = Depends(get_db), ident: IdentityContext = Depends(get_identity_context)):
    validate_client(db, ident, payload.client_id)
    validate_user(db, ident, payload.owner_id)
    obj = CRMOpportunity(organization_id=ident.organization_id, **payload.model_dump())
    db.add(obj)
    commit(db)
    db.refresh(obj)
    return obj


@router.get("/opportunities/{item_id}", response_model=OpportunityRead)
def get_opportunity(item_id: UUID, db: Session = Depends(get_db), ident: IdentityContext = Depends(get_identity_context)):
    return tenant_item(CRMOpportunity, db, ident, item_id)


@router.patch("/opportunities/{item_id}", response_model=OpportunityRead)
def update_opportunity(item_id: UUID, payload: OpportunityUpdate, db: Session = Depends(get_db), ident: IdentityContext = Depends(get_identity_context)):
    obj = tenant_item(CRMOpportunity, db, ident, item_id)
    changes = payload.model_dump(exclude_unset=True)
    if "client_id" in changes:
        validate_client(db, ident, changes["client_id"])
    if "owner_id" in changes:
        validate_user(db, ident, changes["owner_id"])
    for key, value in changes.items():
        setattr(obj, key, value)
    commit(db)
    db.refresh(obj)
    return obj


@router.delete("/opportunities/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_opportunity(item_id: UUID, db: Session = Depends(get_db), ident: IdentityContext = Depends(get_identity_context)):
    db.delete(tenant_item(CRMOpportunity, db, ident, item_id))
    commit(db)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/tasks", response_model=list[TaskRead])
def list_tasks(
    task_status: TaskStatus | None = Query(None, alias="status"),
    priority: TaskPriority | None = None,
    assigned_to_id: UUID | None = None,
    overdue_only: bool = False,
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    ident: IdentityContext = Depends(get_identity_context),
):
    query = select(CRMTask).where(CRMTask.organization_id == ident.organization_id)
    if task_status:
        query = query.where(CRMTask.status == task_status)
    if priority:
        query = query.where(CRMTask.priority == priority)
    if assigned_to_id:
        query = query.where(CRMTask.assigned_to_id == assigned_to_id)
    if overdue_only:
        query = query.where(CRMTask.status.notin_(["completed", "cancelled"]), CRMTask.due_at < datetime.now(timezone.utc))
    return list(db.scalars(query.order_by(CRMTask.due_at.asc().nullslast(), CRMTask.id).offset(offset).limit(limit)))


@router.post("/tasks", response_model=TaskRead, status_code=status.HTTP_201_CREATED)
def create_task(payload: TaskCreate, db: Session = Depends(get_db), ident: IdentityContext = Depends(get_identity_context)):
    validate_client(db, ident, payload.client_id)
    validate_user(db, ident, payload.assigned_to_id)
    if payload.opportunity_id:
        tenant_item(CRMOpportunity, db, ident, payload.opportunity_id)
    obj = CRMTask(organization_id=ident.organization_id, **payload.model_dump())
    if obj.status == "completed":
        obj.completed_at = datetime.now(timezone.utc)
    db.add(obj)
    commit(db)
    db.refresh(obj)
    return obj


@router.get("/tasks/{item_id}", response_model=TaskRead)
def get_task(item_id: UUID, db: Session = Depends(get_db), ident: IdentityContext = Depends(get_identity_context)):
    return tenant_item(CRMTask, db, ident, item_id)


@router.patch("/tasks/{item_id}", response_model=TaskRead)
def update_task(item_id: UUID, payload: TaskUpdate, db: Session = Depends(get_db), ident: IdentityContext = Depends(get_identity_context)):
    obj = tenant_item(CRMTask, db, ident, item_id)
    changes = payload.model_dump(exclude_unset=True)
    if "client_id" in changes:
        validate_client(db, ident, changes["client_id"])
    if "assigned_to_id" in changes:
        validate_user(db, ident, changes["assigned_to_id"])
    if changes.get("opportunity_id"):
        tenant_item(CRMOpportunity, db, ident, changes["opportunity_id"])
    for key, value in changes.items():
        setattr(obj, key, value)
    if "status" in changes:
        obj.completed_at = datetime.now(timezone.utc) if changes["status"] == "completed" else None
    commit(db)
    db.refresh(obj)
    return obj


@router.post("/tasks/{item_id}/complete", response_model=TaskRead)
def complete_task(item_id: UUID, db: Session = Depends(get_db), ident: IdentityContext = Depends(get_identity_context)):
    obj = tenant_item(CRMTask, db, ident, item_id)
    obj.status = "completed"
    obj.completed_at = datetime.now(timezone.utc)
    commit(db)
    db.refresh(obj)
    return obj


@router.delete("/tasks/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task(item_id: UUID, db: Session = Depends(get_db), ident: IdentityContext = Depends(get_identity_context)):
    db.delete(tenant_item(CRMTask, db, ident, item_id))
    commit(db)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/summary", response_model=CRMSummary)
def summary(db: Session = Depends(get_db), ident: IdentityContext = Depends(get_identity_context)):
    org = ident.organization_id
    count = lambda model: db.scalar(select(func.count()).select_from(model).where(model.organization_id == org)) or 0
    open_filter = CRMOpportunity.stage.notin_(["won", "lost"])
    value = db.scalar(select(func.coalesce(func.sum(CRMOpportunity.estimated_value), 0)).where(CRMOpportunity.organization_id == org, open_filter)) or 0
    weighted = db.scalar(select(func.coalesce(func.sum(CRMOpportunity.estimated_value * CRMOpportunity.probability / 100.0), 0)).where(CRMOpportunity.organization_id == org, open_filter)) or 0
    pending = db.scalar(select(func.count()).select_from(CRMTask).where(CRMTask.organization_id == org, CRMTask.status.notin_(["completed", "cancelled"]))) or 0
    overdue = db.scalar(select(func.count()).select_from(CRMTask).where(CRMTask.organization_id == org, CRMTask.status.notin_(["completed", "cancelled"]), CRMTask.due_at < datetime.now(timezone.utc))) or 0
    return CRMSummary(contacts=count(CRMContact), interactions=count(CRMInteraction), opportunities=count(CRMOpportunity), open_pipeline_value=float(value), weighted_pipeline_value=float(weighted), pending_tasks=pending, overdue_tasks=overdue)
