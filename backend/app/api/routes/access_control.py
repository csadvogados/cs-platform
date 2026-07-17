from __future__ import annotations

import uuid
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.api.deps import get_current_user, require_roles
from app.core.security import hash_password, hash_token
from app.db.session import get_db
from app.models.access_control import Permission, Role, UserInvitation, UserSession
from app.models.user import User
from app.schemas.access_control import *
from app.services.access_control import create_invitation
from app.services.audit import record_audit

roles_router = APIRouter()
permissions_router = APIRouter()
invitations_router = APIRouter()
sessions_router = APIRouter()

@permissions_router.get("", response_model=list[PermissionRead])
def list_permissions(db: Session=Depends(get_db), actor: User=Depends(require_roles("admin"))):
    return list(db.scalars(select(Permission).order_by(Permission.module, Permission.code)))

@roles_router.get("", response_model=list[RoleRead])
def list_roles(db: Session=Depends(get_db), actor: User=Depends(require_roles("admin", "supervisor"))):
    return list(db.scalars(select(Role).options(selectinload(Role.permissions)).where(Role.organization_id==actor.organization_id).order_by(Role.name)))

@roles_router.post("", response_model=RoleRead, status_code=201)
def create_role(payload: RoleCreate, db: Session=Depends(get_db), actor: User=Depends(require_roles("admin"))):
    if db.scalar(select(Role).where(Role.organization_id==actor.organization_id, Role.slug==payload.slug)):
        raise HTTPException(409, "Perfil já existe")
    perms=list(db.scalars(select(Permission).where(Permission.code.in_(payload.permission_codes)))) if payload.permission_codes else []
    if len(perms)!=len(set(payload.permission_codes)): raise HTTPException(422, "Uma ou mais permissões são inválidas")
    role=Role(organization_id=actor.organization_id,name=payload.name,slug=payload.slug,description=payload.description,permissions=perms)
    db.add(role); db.flush(); record_audit(db, organization_id=actor.organization_id,user_id=actor.id,entity_type="role",entity_id=role.id,action="create",new_values={"slug":role.slug}); db.commit(); db.refresh(role); return role

@roles_router.patch("/{role_id}", response_model=RoleRead)
def update_role(role_id: uuid.UUID,payload:RoleUpdate,db:Session=Depends(get_db),actor:User=Depends(require_roles("admin"))):
    role=db.scalar(select(Role).options(selectinload(Role.permissions)).where(Role.id==role_id,Role.organization_id==actor.organization_id))
    if not role: raise HTTPException(404,"Perfil não encontrado")
    if payload.name is not None: role.name=payload.name
    if payload.description is not None: role.description=payload.description
    if payload.is_active is not None: role.is_active=payload.is_active
    if payload.permission_codes is not None:
        perms=list(db.scalars(select(Permission).where(Permission.code.in_(payload.permission_codes)))) if payload.permission_codes else []
        if len(perms)!=len(set(payload.permission_codes)): raise HTTPException(422,"Uma ou mais permissões são inválidas")
        role.permissions=perms
    record_audit(db,organization_id=actor.organization_id,user_id=actor.id,entity_type="role",entity_id=role.id,action="update"); db.commit(); db.refresh(role); return role

@invitations_router.post("", response_model=InvitationCreated, status_code=201)
def invite(payload:InvitationCreate,db:Session=Depends(get_db),actor:User=Depends(require_roles("admin"))):
    if db.scalar(select(User).where(User.organization_id==actor.organization_id,User.email==payload.email.lower(),User.deleted_at.is_(None))): raise HTTPException(409,"E-mail já cadastrado")
    if payload.role_id and not db.scalar(select(Role).where(Role.id==payload.role_id,Role.organization_id==actor.organization_id)): raise HTTPException(422,"Perfil inválido")
    inv,token=create_invitation(db,organization_id=actor.organization_id,created_by_id=actor.id,email=payload.email,full_name=payload.full_name,role_id=payload.role_id,hours=payload.expires_in_hours)
    record_audit(db,organization_id=actor.organization_id,user_id=actor.id,entity_type="invitation",entity_id=inv.id,action="create",new_values={"email":inv.email}); db.commit(); db.refresh(inv)
    data=InvitationRead.model_validate(inv).model_dump(); return InvitationCreated(**data,token=token)

@invitations_router.get("", response_model=list[InvitationRead])
def invitations(db:Session=Depends(get_db),actor:User=Depends(require_roles("admin"))):
    return list(db.scalars(select(UserInvitation).where(UserInvitation.organization_id==actor.organization_id).order_by(UserInvitation.created_at.desc())))

@invitations_router.post("/accept", response_model=dict, status_code=201)
def accept_invitation(payload:InvitationAccept,db:Session=Depends(get_db)):
    now=datetime.now(timezone.utc); inv=db.scalar(select(UserInvitation).where(UserInvitation.token_hash==hash_token(payload.token)))
    expires_at = inv.expires_at
    if expires_at and expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    if not inv or inv.accepted_at or inv.revoked_at or expires_at <= now: raise HTTPException(400,"Convite inválido ou expirado")
    if db.scalar(select(User).where(User.organization_id==inv.organization_id,User.email==inv.email,User.deleted_at.is_(None))): raise HTTPException(409,"E-mail já cadastrado")
    user=User(organization_id=inv.organization_id,full_name=inv.full_name,email=inv.email,password_hash=hash_password(payload.password),role="atendimento",status="active",must_change_password=False,password_changed_at=now)
    if inv.role: user.roles=[inv.role]; user.role=inv.role.slug if inv.role.slug in {"admin","supervisor","advogado","negociador","financeiro","atendimento"} else "atendimento"
    db.add(user); inv.accepted_at=now; db.flush(); record_audit(db,organization_id=inv.organization_id,user_id=user.id,entity_type="invitation",entity_id=inv.id,action="accept"); db.commit(); return {"user_id":str(user.id),"status":"active"}

@sessions_router.get("", response_model=list[SessionRead])
def my_sessions(db:Session=Depends(get_db),actor:User=Depends(get_current_user)):
    return list(db.scalars(select(UserSession).where(UserSession.user_id==actor.id).order_by(UserSession.created_at.desc())))

@sessions_router.delete("/{session_id}", status_code=204)
def revoke_session(session_id:uuid.UUID,db:Session=Depends(get_db),actor:User=Depends(get_current_user)):
    session=db.scalar(select(UserSession).where(UserSession.id==session_id,UserSession.user_id==actor.id))
    if not session: raise HTTPException(404,"Sessão não encontrada")
    session.revoked_at=datetime.now(timezone.utc); db.commit(); return None
