import secrets
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Header, HTTPException, status
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import hash_password
from app.db.session import get_db
from app.models.refresh_token import RefreshToken
from app.models.user import User

router = APIRouter()

class AdminRecoveryRequest(BaseModel):
    email: EmailStr | None = None
    new_password: str = Field(min_length=12, max_length=128)

class AdminRecoveryResponse(BaseModel):
    status: str
    email: EmailStr
    message: str

@router.post('/reset-admin', response_model=AdminRecoveryResponse)
def reset_admin(
    payload: AdminRecoveryRequest,
    db: Session = Depends(get_db),
    x_admin_recovery_key: str | None = Header(default=None, alias='X-Admin-Recovery-Key'),
):
    if not settings.admin_recovery_enabled:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Endpoint indisponível')

    configured_key = settings.admin_recovery_key or ''
    if (not x_admin_recovery_key or not configured_key or
        not secrets.compare_digest(x_admin_recovery_key, configured_key)):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail='Chave de recuperação inválida')

    if payload.email:
        user = db.scalar(select(User).where(User.email == payload.email.strip().lower()))
    else:
        user = db.scalar(select(User).where(User.is_superuser.is_(True)).order_by(User.created_at.asc()).limit(1))

    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Administrador não encontrado')

    user.password_hash = hash_password(payload.new_password)
    user.failed_login_attempts = 0
    user.locked_until = None
    user.status = 'active'
    user.must_change_password = False

    db.execute(
        update(RefreshToken)
        .where(RefreshToken.user_id == user.id, RefreshToken.revoked.is_(False))
        .values(revoked=True, revoked_at=datetime.now(timezone.utc))
    )
    db.commit()

    return AdminRecoveryResponse(
        status='ok',
        email=user.email,
        message='Senha administrativa redefinida. Desative imediatamente o endpoint de recuperação.',
    )
