import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.deps import require_permissions
from app.db.session import get_db
from app.models.client import Client
from app.schemas.client import ClientCreate, ClientRead, ClientUpdate
from app.security.identity import IdentityContext
from app.security.permissions import PermissionCode
from app.services.audit import record_audit

router = APIRouter()


@router.post("", response_model=ClientRead, status_code=status.HTTP_201_CREATED)
def create_client(
    payload: ClientCreate,
    db: Session = Depends(get_db),
    actor: IdentityContext = Depends(
        require_permissions(PermissionCode.CLIENT_CREATE.value)
    ),
):
    client = Client(
        organization_id=actor.organization_id,
        **payload.model_dump(mode="json"),
    )
    db.add(client)
    try:
        db.flush()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="CPF já cadastrado nesta organização",
        ) from exc
    record_audit(
        db,
        organization_id=actor.organization_id,
        user_id=actor.user_id,
        entity_type="client",
        entity_id=client.id,
        action="create",
        new_values={
            "full_name": client.full_name,
            "cpf": client.cpf,
            "status": client.status,
        },
    )
    db.commit()
    db.refresh(client)
    return client


@router.get("", response_model=list[ClientRead])
def list_clients(
    q: str | None = None,
    client_status: str | None = Query(default=None, alias="status"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    actor: IdentityContext = Depends(
        require_permissions(PermissionCode.CLIENT_READ.value)
    ),
):
    stmt = select(Client).where(Client.organization_id == actor.organization_id)
    if q:
        term = f"%{q.strip()}%"
        stmt = stmt.where(
            or_(
                Client.full_name.ilike(term),
                Client.cpf.ilike(term),
                Client.phone.ilike(term),
            )
        )
    if client_status:
        stmt = stmt.where(Client.status == client_status)
    stmt = stmt.order_by(Client.created_at.desc()).limit(limit).offset(offset)
    return list(db.scalars(stmt))


@router.get("/{client_id}", response_model=ClientRead)
def get_client(
    client_id: uuid.UUID,
    db: Session = Depends(get_db),
    actor: IdentityContext = Depends(
        require_permissions(PermissionCode.CLIENT_READ.value)
    ),
):
    client = db.scalar(
        select(Client).where(
            Client.id == client_id,
            Client.organization_id == actor.organization_id,
        )
    )
    if not client:
        raise HTTPException(status_code=404, detail="Cliente não encontrado")
    return client


@router.patch("/{client_id}", response_model=ClientRead)
def update_client(
    client_id: uuid.UUID,
    payload: ClientUpdate,
    db: Session = Depends(get_db),
    actor: IdentityContext = Depends(
        require_permissions(PermissionCode.CLIENT_UPDATE.value)
    ),
):
    client = db.scalar(
        select(Client).where(
            Client.id == client_id,
            Client.organization_id == actor.organization_id,
        )
    )
    if not client:
        raise HTTPException(status_code=404, detail="Cliente não encontrado")
    changes = payload.model_dump(exclude_unset=True, mode="json")
    old_values = {key: getattr(client, key) for key in changes}
    for key, value in changes.items():
        setattr(client, key, value)
    record_audit(
        db,
        organization_id=actor.organization_id,
        user_id=actor.user_id,
        entity_type="client",
        entity_id=client.id,
        action="update",
        old_values={key: str(value) if isinstance(value, uuid.UUID) else value for key, value in old_values.items()},
        new_values={key: str(value) if isinstance(value, uuid.UUID) else value for key, value in changes.items()},
    )
    db.commit()
    db.refresh(client)
    return client
