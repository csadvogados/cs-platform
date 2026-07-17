from __future__ import annotations

import secrets
from datetime import datetime, timedelta, timezone
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import hash_token
from app.models.access_control import Permission, Role, UserInvitation
from app.security.permissions import PermissionCode

DEFAULT_ROLES = {
    "admin": set(PermissionCode.values()),
    "supervisor": {"user.read", "client.create", "client.read", "client.update", "dashboard.read", "report.read", "audit.read"},
    "advogado": {"client.create", "client.read", "client.update", "debt.read", "diagnosis.create", "diagnosis.read", "document.read", "document.upload", "dashboard.read"},
    "negociador": {"client.read", "client.update", "debt.read", "debt.update", "negotiation.create", "negotiation.read", "negotiation.update", "dashboard.read"},
    "financeiro": {"client.read", "creditor.read", "debt.read", "debt.update", "report.read", "report.export", "dashboard.read"},
    "atendimento": {"client.create", "client.read", "client.update", "document.upload", "document.read", "dashboard.read"},
    "consulta": {"client.read", "debt.read", "diagnosis.read", "document.read", "dashboard.read"},
}


def seed_permissions_and_roles(db: Session, organization_id) -> None:
    permissions_by_code = {x.code: x for x in db.scalars(select(Permission)).all()}
    for code in PermissionCode.values():
        if code not in permissions_by_code:
            module = code.split('.', 1)[0]
            obj = Permission(code=code, name=code.replace('.', ' ').replace('_', ' ').title(), module=module)
            db.add(obj); permissions_by_code[code] = obj
    db.flush()
    existing = {x.slug: x for x in db.scalars(select(Role).where(Role.organization_id == organization_id)).all()}
    for slug, codes in DEFAULT_ROLES.items():
        role = existing.get(slug)
        if role is None:
            role = Role(organization_id=organization_id, name=slug.replace('_',' ').title(), slug=slug, is_system=True)
            db.add(role)
        role.permissions = [permissions_by_code[c] for c in codes if c in permissions_by_code]
    db.flush()


def create_invitation(db: Session, *, organization_id, created_by_id, email: str, full_name: str, role_id, hours: int):
    token = secrets.token_urlsafe(32)
    invitation = UserInvitation(
        organization_id=organization_id, created_by_id=created_by_id,
        email=email.strip().lower(), full_name=full_name.strip(), role_id=role_id,
        token_hash=hash_token(token), expires_at=datetime.now(timezone.utc)+timedelta(hours=hours),
    )
    db.add(invitation); db.flush()
    return invitation, token
