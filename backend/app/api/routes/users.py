import uuid
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, or_, select, update
from sqlalchemy.orm import Session, selectinload
from app.api.deps import require_roles
from app.core.security import hash_password
from app.db.session import get_db
from app.models.access_control import Role, UserSession
from app.models.refresh_token import RefreshToken
from app.models.user import User
from app.schemas.user import ALLOWED_ROLES, UserCreate, UserPage, UserRead, UserUpdate
from app.services.audit import record_audit

router=APIRouter()

def _get_user(db,user_id,org_id):
    user=db.scalar(select(User).options(selectinload(User.roles)).where(User.id==user_id,User.organization_id==org_id,User.deleted_at.is_(None)))
    if not user: raise HTTPException(404,"Usuário não encontrado")
    return user

@router.post("",response_model=UserRead,status_code=201)
def create_user(payload:UserCreate,db:Session=Depends(get_db),actor:User=Depends(require_roles("admin"))):
    if payload.role not in ALLOWED_ROLES: raise HTTPException(422,"Perfil de usuário inválido")
    email=payload.email.lower()
    if db.scalar(select(User).where(User.organization_id==actor.organization_id,User.email==email,User.deleted_at.is_(None))): raise HTTPException(409,"E-mail já cadastrado")
    roles=list(db.scalars(select(Role).where(Role.organization_id==actor.organization_id,Role.id.in_(payload.role_ids)))) if payload.role_ids else []
    if len(roles)!=len(set(payload.role_ids)): raise HTTPException(422,"Um ou mais perfis são inválidos")
    user=User(organization_id=actor.organization_id,full_name=payload.full_name,email=email,password_hash=hash_password(payload.password),role=payload.role,must_change_password=True,roles=roles)
    db.add(user); db.flush(); record_audit(db,organization_id=actor.organization_id,user_id=actor.id,entity_type="user",entity_id=user.id,action="create",new_values={"email":user.email,"role":user.role}); db.commit(); db.refresh(user); return user

@router.get("",response_model=UserPage)
def list_users(q:str|None=None,status_filter:str|None=Query(None,alias="status"),page:int=Query(1,ge=1),page_size:int=Query(25,ge=1,le=100),db:Session=Depends(get_db),actor:User=Depends(require_roles("admin","supervisor","advogado"))):
    filters=[User.organization_id==actor.organization_id,User.deleted_at.is_(None)]
    if q: filters.append(or_(User.full_name.ilike(f"%{q}%"),User.email.ilike(f"%{q}%")))
    if status_filter: filters.append(User.status==status_filter)
    total=db.scalar(select(func.count()).select_from(User).where(*filters)) or 0
    items=list(db.scalars(select(User).where(*filters).order_by(User.full_name).offset((page-1)*page_size).limit(page_size)))
    return UserPage(items=items,total=total,page=page,page_size=page_size)

@router.get("/{user_id}",response_model=UserRead)
def get_user(user_id:uuid.UUID,db:Session=Depends(get_db),actor:User=Depends(require_roles("admin","supervisor"))): return _get_user(db,user_id,actor.organization_id)

@router.patch("/{user_id}",response_model=UserRead)
def update_user(user_id:uuid.UUID,payload:UserUpdate,db:Session=Depends(get_db),actor:User=Depends(require_roles("admin"))):
    user=_get_user(db,user_id,actor.organization_id)
    if payload.role is not None:
        if payload.role not in ALLOWED_ROLES: raise HTTPException(422,"Perfil de usuário inválido")
        user.role=payload.role
    if payload.full_name is not None:user.full_name=payload.full_name
    if payload.status is not None:
        if payload.status not in {"active","inactive"}: raise HTTPException(422,"Status inválido")
        user.status=payload.status
    if payload.role_ids is not None:
        roles=list(db.scalars(select(Role).where(Role.organization_id==actor.organization_id,Role.id.in_(payload.role_ids)))) if payload.role_ids else []
        if len(roles)!=len(set(payload.role_ids)): raise HTTPException(422,"Um ou mais perfis são inválidos")
        user.roles=roles
    record_audit(db,organization_id=actor.organization_id,user_id=actor.id,entity_type="user",entity_id=user.id,action="update"); db.commit(); db.refresh(user); return user

@router.post("/{user_id}/block",response_model=UserRead)
def block_user(user_id:uuid.UUID,db:Session=Depends(get_db),actor:User=Depends(require_roles("admin"))):
    user=_get_user(db,user_id,actor.organization_id)
    if user.id==actor.id: raise HTTPException(400,"Não é possível bloquear a própria conta")
    user.status="inactive"; now=datetime.now(timezone.utc)
    db.execute(update(RefreshToken).where(RefreshToken.user_id==user.id,RefreshToken.revoked.is_(False)).values(revoked=True,revoked_at=now))
    db.execute(update(UserSession).where(UserSession.user_id==user.id,UserSession.revoked_at.is_(None)).values(revoked_at=now))
    record_audit(db,organization_id=actor.organization_id,user_id=actor.id,entity_type="user",entity_id=user.id,action="block"); db.commit();db.refresh(user);return user

@router.post("/{user_id}/unblock",response_model=UserRead)
def unblock_user(user_id:uuid.UUID,db:Session=Depends(get_db),actor:User=Depends(require_roles("admin"))):
    user=_get_user(db,user_id,actor.organization_id); user.status="active";user.failed_login_attempts=0;user.locked_until=None
    record_audit(db,organization_id=actor.organization_id,user_id=actor.id,entity_type="user",entity_id=user.id,action="unblock");db.commit();db.refresh(user);return user

@router.delete("/{user_id}",status_code=204)
def delete_user(user_id:uuid.UUID,db:Session=Depends(get_db),actor:User=Depends(require_roles("admin"))):
    user=_get_user(db,user_id,actor.organization_id)
    if user.id==actor.id: raise HTTPException(400,"Não é possível excluir a própria conta")
    user.deleted_at=datetime.now(timezone.utc);user.status="inactive"
    record_audit(db,organization_id=actor.organization_id,user_id=actor.id,entity_type="user",entity_id=user.id,action="delete");db.commit();return None
