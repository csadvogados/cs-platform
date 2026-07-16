import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import require_roles
from app.core.security import hash_password
from app.db.session import get_db
from app.models.user import User
from app.schemas.user import (
    ALLOWED_ROLES,
    UserCreate,
    UserRead,
    UserUpdate,
)
from app.services.audit import record_audit


router = APIRouter()


@router.post(
    "",
    response_model=UserRead,
    status_code=status.HTTP_201_CREATED,
)
def create_user(
    payload: UserCreate,
    db: Session = Depends(get_db),
    actor: User = Depends(require_roles("admin")),
):
    if payload.role not in ALLOWED_ROLES:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Perfil de usuário inválido",
        )

    email = payload.email.lower()

    existing = db.scalar(
        select(User).where(
            User.organization_id == actor.organization_id,
            User.email == email,
        )
    )

    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="E-mail já cadastrado",
        )

    user = User(
        organization_id=actor.organization_id,
        full_name=payload.full_name,
        email=email,
        password_hash=hash_password(payload.password),
        role=payload.role,
        must_change_password=True,
    )

    db.add(user)
    db.flush()

    record_audit(
        db,
        organization_id=actor.organization_id,
        user_id=actor.id,
        entity_type="user",
        entity_id=user.id,
        action="create",
        new_values={
            "email": user.email,
            "role": user.role,
        },
    )

    db.commit()
    db.refresh(user)
    return user


@router.get("", response_model=list[UserRead])
def list_users(
    db: Session = Depends(get_db),
    actor: User = Depends(
        require_roles("admin", "supervisor", "advogado")
    ),
):
    return list(
        db.scalars(
            select(User)
            .where(
                User.organization_id == actor.organization_id
            )
            .order_by(User.full_name)
        )
    )


@router.patch("/{user_id}", response_model=UserRead)
def update_user(
    user_id: uuid.UUID,
    payload: UserUpdate,
    db: Session = Depends(get_db),
    actor: User = Depends(require_roles("admin")),
):
    user = db.get(User, user_id)

    if (
        not user
        or user.organization_id != actor.organization_id
    ):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuário não encontrado",
        )

    if payload.role is not None:
        if payload.role not in ALLOWED_ROLES:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Perfil de usuário inválido",
            )
        user.role = payload.role

    if payload.full_name is not None:
        user.full_name = payload.full_name

    if payload.status is not None:
        if payload.status not in {"active", "inactive"}:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Status inválido",
            )
        user.status = payload.status

    record_audit(
        db,
        organization_id=actor.organization_id,
        user_id=actor.id,
        entity_type="user",
        entity_id=user.id,
        action="update",
        new_values={
            "full_name": user.full_name,
            "role": user.role,
            "status": user.status,
        },
    )

    db.commit()
    db.refresh(user)
    return user
