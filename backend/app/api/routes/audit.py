from __future__ import annotations

import uuid
from datetime import date, datetime, time, timezone
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.api.deps import require_permissions
from app.db.session import get_db
from app.models.audit import AuditEvent
from app.models.user import User
from app.schemas.audit import AuditEventRead, AuditPage
from app.security.identity import IdentityContext
from app.security.permissions import PermissionCode


router = APIRouter()


def sanitized_value(key: str, value: Any) -> Any:
    normalized = key.strip().lower()
    if any(part in normalized for part in ("password", "token", "secret", "hash")):
        return "[PROTEGIDO]"
    if normalized in {"cpf", "tax_id", "cnpj"}:
        digits = "".join(character for character in str(value or "") if character.isdigit())
        return f"final {digits[-4:]}" if digits else "[PROTEGIDO]"
    if isinstance(value, dict):
        return {nested_key: sanitized_value(nested_key, nested_value) for nested_key, nested_value in value.items()}
    if isinstance(value, list):
        return [sanitized_value(key, item) for item in value]
    return value


def sanitized_details(values: dict[str, Any] | None) -> dict[str, Any] | None:
    if not values:
        return None
    sanitized: dict[str, Any] = {}
    for key, value in values.items():
        normalized = key.strip().lower()
        sanitized[key] = sanitized_value(normalized, value)
    return sanitized


@router.get("", response_model=AuditPage)
def list_audit_events(
    q: str | None = Query(default=None, max_length=200),
    entity_type: str | None = Query(default=None, max_length=80),
    action: str | None = Query(default=None, max_length=40),
    user_id: uuid.UUID | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=25, ge=1, le=100),
    db: Session = Depends(get_db),
    identity: IdentityContext = Depends(require_permissions(PermissionCode.AUDIT_READ.value)),
):
    if date_from and date_to and date_from > date_to:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="A data inicial não pode ser posterior à data final",
        )

    conditions = [AuditEvent.organization_id == identity.organization_id]
    if entity_type:
        conditions.append(AuditEvent.entity_type == entity_type.strip().lower())
    if action:
        conditions.append(AuditEvent.action == action.strip().lower())
    if user_id:
        conditions.append(AuditEvent.user_id == user_id)
    if date_from:
        conditions.append(
            AuditEvent.occurred_at >= datetime.combine(date_from, time.min, tzinfo=timezone.utc)
        )
    if date_to:
        conditions.append(
            AuditEvent.occurred_at <= datetime.combine(date_to, time.max, tzinfo=timezone.utc)
        )
    if q and q.strip():
        term = f"%{q.strip()}%"
        conditions.append(
            or_(
                User.full_name.ilike(term),
                User.email.ilike(term),
                AuditEvent.entity_type.ilike(term),
                AuditEvent.action.ilike(term),
            )
        )

    base = (
        select(AuditEvent, User.full_name, User.email)
        .outerjoin(User, User.id == AuditEvent.user_id)
        .where(*conditions)
    )
    total = db.scalar(
        select(func.count())
        .select_from(AuditEvent)
        .outerjoin(User, User.id == AuditEvent.user_id)
        .where(*conditions)
    ) or 0
    rows = db.execute(
        base.order_by(AuditEvent.occurred_at.desc(), AuditEvent.id.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    ).all()

    items = [
        AuditEventRead(
            id=event.id,
            user_id=event.user_id,
            actor_name=user_name or ("Sistema" if event.user_id is None else "Usuário removido"),
            actor_email=user_email,
            entity_type=event.entity_type,
            entity_id=event.entity_id,
            action=event.action,
            details=sanitized_details(event.new_values),
            occurred_at=event.occurred_at,
        )
        for event, user_name, user_email in rows
    ]
    return AuditPage(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        pages=(total + page_size - 1) // page_size if total else 0,
    )
