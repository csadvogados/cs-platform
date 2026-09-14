from datetime import datetime, timedelta, timezone
import uuid

import jwt
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_identity_context
from app.core.config import settings
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_refresh_token,
    hash_password,
    hash_token,
    verify_password,
)
from app.db.session import get_db
from app.models.refresh_token import RefreshToken
from app.models.access_control import PasswordHistory, UserSession
from app.models.user import User
from app.schemas.auth import (
    ChangePasswordRequest,
    LoginRequest,
    LogoutRequest,
    RefreshRequest,
    TokenPair,
)
from app.schemas.identity import IdentityRead
from app.schemas.user import UserRead
from app.security.identity import IdentityContext
from app.services.audit import record_audit


router = APIRouter()


def _issue_tokens(db: Session, user: User) -> TokenPair:
    extra = {
        "org": str(user.organization_id),
        "role": user.role,
    }

    access_token = create_access_token(
        str(user.id),
        extra,
    )
    refresh_token = create_refresh_token(
        str(user.id),
        extra,
    )

    expires_at = datetime.now(timezone.utc) + timedelta(
        days=settings.refresh_token_expire_days
    )

    refresh_hash = hash_token(refresh_token)
    db.add(
        RefreshToken(
            user_id=user.id,
            token_hash=refresh_hash,
            expires_at=expires_at,
        )
    )
    db.add(
        UserSession(
            organization_id=user.organization_id,
            user_id=user.id,
            refresh_token_hash=refresh_hash,
            last_activity_at=datetime.now(timezone.utc),
            expires_at=expires_at,
        )
    )

    return TokenPair(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=settings.access_token_expire_minutes * 60,
        must_change_password=user.must_change_password,
    )


def _authenticate(
    db: Session,
    email: str,
    password: str,
) -> User:
    now = datetime.now(timezone.utc)
    normalized_email = email.strip().lower()

    user = db.scalar(
        select(User).where(User.email == normalized_email)
    )

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="E-mail ou senha inválidos",
        )

    if user.status != "active":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Usuário inativo",
        )

    if user.locked_until and user.locked_until > now:
        raise HTTPException(
            status_code=status.HTTP_423_LOCKED,
            detail="Usuário temporariamente bloqueado",
        )

    if not verify_password(password, user.password_hash):
        user.failed_login_attempts += 1

        if (
            user.failed_login_attempts
            >= settings.max_failed_login_attempts
        ):
            user.locked_until = now + timedelta(
                minutes=settings.login_lock_minutes
            )
            user.failed_login_attempts = 0

        db.commit()

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="E-mail ou senha inválidos",
        )

    user.failed_login_attempts = 0
    user.locked_until = None
    user.last_login_at = now

    return user


@router.post("/login", response_model=TokenPair)
def login_json(
    payload: LoginRequest,
    db: Session = Depends(get_db),
):
    user = _authenticate(
        db,
        payload.email,
        payload.password,
    )

    tokens = _issue_tokens(db, user)

    record_audit(
        db,
        organization_id=user.organization_id,
        user_id=user.id,
        entity_type="auth",
        entity_id=user.id,
        action="login",
        new_values={"email": user.email},
    )

    db.commit()
    return tokens


@router.post("/token", response_model=TokenPair)
def login_oauth(
    form: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    user = _authenticate(
        db,
        form.username,
        form.password,
    )

    tokens = _issue_tokens(db, user)
    db.commit()
    return tokens


@router.post("/refresh", response_model=TokenPair)
def refresh(
    payload: RefreshRequest,
    db: Session = Depends(get_db),
):
    try:
        decoded = decode_refresh_token(
            payload.refresh_token
        )
        user_id = uuid.UUID(decoded["sub"])
    except (jwt.PyJWTError, KeyError, ValueError, TypeError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token inválido",
        )

    token_hash_value = hash_token(payload.refresh_token)
    stored = db.scalar(
        select(RefreshToken).where(
            RefreshToken.token_hash == token_hash_value,
            RefreshToken.revoked.is_(False),
        )
    )

    now = datetime.now(timezone.utc)

    if not stored or stored.expires_at <= now:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token expirado ou revogado",
        )

    user = db.get(User, user_id)

    if not user or user.status != "active":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuário inválido",
        )

    stored.revoked = True
    stored.revoked_at = now

    tokens = _issue_tokens(db, user)
    db.commit()

    return tokens


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(
    payload: LogoutRequest,
    db: Session = Depends(get_db),
):
    token_hash_value = hash_token(payload.refresh_token)

    stored = db.scalar(
        select(RefreshToken).where(
            RefreshToken.token_hash == token_hash_value
        )
    )

    if stored and not stored.revoked:
        now = datetime.now(timezone.utc)
        stored.revoked = True
        stored.revoked_at = now
        session = db.scalar(
            select(UserSession).where(
                UserSession.refresh_token_hash == token_hash_value
            )
        )
        if session and not session.revoked_at:
            session.revoked_at = now
        db.commit()

    return None


@router.get("/me", response_model=IdentityRead)
def me(
    identity: IdentityContext = Depends(get_identity_context),
):
    user = identity.user
    return IdentityRead(
        id=user.id,
        organization_id=user.organization_id,
        full_name=user.full_name,
        email=user.email,
        role=user.role,
        status=user.status,
        is_superuser=user.is_superuser,
        must_change_password=user.must_change_password,
        permissions=sorted(identity.permissions),
        organization=identity.organization,
    )


@router.post(
    "/change-password",
    status_code=status.HTTP_204_NO_CONTENT,
)
def change_password(
    payload: ChangePasswordRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    if not verify_password(
        payload.current_password,
        user.password_hash,
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Senha atual incorreta",
        )

    if payload.current_password == payload.new_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A nova senha deve ser diferente",
        )

    now = datetime.now(timezone.utc)
    db.add(
        PasswordHistory(
            user_id=user.id,
            password_hash=user.password_hash,
            created_at=now,
        )
    )
    user.password_hash = hash_password(payload.new_password)
    user.must_change_password = False
    user.password_changed_at = now

    db.execute(
        update(RefreshToken)
        .where(
            RefreshToken.user_id == user.id,
            RefreshToken.revoked.is_(False),
        )
        .values(
            revoked=True,
            revoked_at=datetime.now(timezone.utc),
        )
    )

    record_audit(
        db,
        organization_id=user.organization_id,
        user_id=user.id,
        entity_type="auth",
        entity_id=user.id,
        action="change_password",
    )

    db.commit()
    return None
