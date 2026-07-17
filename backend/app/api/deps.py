from __future__ import annotations

import uuid
from collections.abc import Callable

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session, joinedload

from app.core.security import decode_access_token
from app.db.session import get_db
from app.models.organization_enums import OrganizationStatus
from app.models.user import User
from app.security.identity import IdentityContext
from app.security.rbac import RolePermissionRegistry


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/token")


def _authentication_error(detail: str = "Credenciais inválidas") -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=detail,
        headers={"WWW-Authenticate": "Bearer"},
    )


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    try:
        payload = decode_access_token(token)
        user_id = uuid.UUID(str(payload.get("sub", "")))
    except (jwt.PyJWTError, ValueError, TypeError) as exc:
        raise _authentication_error() from exc

    user = db.get(
        User,
        user_id,
        options=(joinedload(User.organization),),
    )
    if not user or user.status != "active":
        raise _authentication_error()

    organization = user.organization
    if not organization or organization.status != OrganizationStatus.ACTIVE.value:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Organização inativa ou indisponível",
        )

    # Claims are hints, not the source of truth. A mismatch invalidates stale or
    # tampered tokens; authorization still uses the current database values.
    claim_org = payload.get("org")
    claim_role = payload.get("role")
    if claim_org and str(user.organization_id) != str(claim_org):
        raise _authentication_error("Token incompatível com a organização atual")
    if claim_role and str(user.role) != str(claim_role):
        raise _authentication_error("Token incompatível com o perfil atual")

    return user


def get_identity_context(
    user: User = Depends(get_current_user),
) -> IdentityContext:
    return IdentityContext.from_entities(
        user=user,
        organization=user.organization,
    )


def require_superuser(
    identity: IdentityContext = Depends(get_identity_context),
) -> IdentityContext:
    if not identity.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Operação exclusiva de superadministrador",
        )
    return identity


def require_roles(*roles: str) -> Callable[..., User]:
    normalized_roles = {role.strip().lower() for role in roles}

    def checker(user: User = Depends(get_current_user)) -> User:
        if not user.is_superuser and user.role.strip().lower() not in normalized_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Permissão insuficiente",
            )
        return user

    return checker


def require_permissions(*permissions: str) -> Callable[..., IdentityContext]:
    normalized = tuple(str(permission) for permission in permissions)

    def checker(
        identity: IdentityContext = Depends(get_identity_context),
    ) -> IdentityContext:
        if identity.is_superuser:
            return identity
        if not all(
            RolePermissionRegistry.has_permission(identity.role, permission)
            for permission in normalized
        ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Permissão insuficiente",
            )
        return identity

    return checker


__all__ = [
    "get_current_user",
    "get_identity_context",
    "require_superuser",
    "require_roles",
    "require_permissions",
]
