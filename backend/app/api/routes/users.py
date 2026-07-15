from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.api.deps import require_roles
from app.core.security import hash_password
from app.db.session import get_db
from app.models.user import User
from app.schemas.user import UserCreate, UserRead
from app.services.audit import record_audit

router = APIRouter()

@router.post("", response_model=UserRead, status_code=status.HTTP_201_CREATED)
def create_user(payload: UserCreate, db: Session = Depends(get_db), actor: User = Depends(require_roles("admin"))):
    email = payload.email.lower()
    if db.scalar(select(User).where(User.organization_id == actor.organization_id, User.email == email)):
        raise HTTPException(status_code=409, detail="E-mail já cadastrado")
    user = User(organization_id=actor.organization_id, full_name=payload.full_name, email=email, password_hash=hash_password(payload.password), role=payload.role)
    db.add(user); db.flush()
    record_audit(db, organization_id=actor.organization_id, user_id=actor.id, entity_type="user", entity_id=user.id, action="create", new_values={"email":user.email,"role":user.role})
    db.commit(); db.refresh(user)
    return user

@router.get("", response_model=list[UserRead])
def list_users(db: Session = Depends(get_db), actor: User = Depends(require_roles("admin","lawyer"))):
    return list(db.scalars(select(User).where(User.organization_id == actor.organization_id).order_by(User.full_name)))
