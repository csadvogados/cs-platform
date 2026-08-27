import uuid
from datetime import date, datetime, time, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select, update
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.api.routes.performance import build_overview
from app.db.session import get_db
from app.models.crm import CRMTask
from app.models.financial import CollectionAction, PaymentInstallment
from app.models.notification import Notification, NotificationPreference
from app.models.user import User
from app.schemas.notification import (
    NotificationPage, NotificationPreferencesRead, NotificationPreferencesUpdate,
    NotificationRead, NotificationStatusUpdate,
)
from app.security.identity import IdentityContext
from app.services.audit import record_audit


router = APIRouter()


def utc_value(value: datetime | None) -> datetime | None:
    if value is None:
        return None
    return value if value.tzinfo else value.replace(tzinfo=timezone.utc)


def get_preferences(db: Session, actor: User) -> NotificationPreference:
    preference = db.scalar(select(NotificationPreference).where(NotificationPreference.user_id == actor.id))
    if preference:
        return preference
    preference = NotificationPreference(organization_id=actor.organization_id, user_id=actor.id)
    db.add(preference)
    db.flush()
    return preference


def add_notification(db: Session, actor: User, *, key: str, kind: str, priority: str, title: str, message: str, event_at: datetime, target_view: str, target_filter: str) -> None:
    exists = db.scalar(select(Notification.id).where(
        Notification.user_id == actor.id,
        Notification.deduplication_key == key,
    ))
    if exists:
        return
    db.add(Notification(
        organization_id=actor.organization_id, user_id=actor.id,
        notification_type=kind, priority=priority, title=title, message=message,
        target_view=target_view, target_filter=target_filter,
        deduplication_key=key, event_at=event_at,
    ))


def synchronize_notifications(db: Session, actor: User) -> None:
    preferences = get_preferences(db, actor)
    now = datetime.now(timezone.utc)
    today = now.date()
    soon = now + timedelta(days=2)

    if preferences.tasks_enabled:
        query = select(CRMTask).where(
            CRMTask.organization_id == actor.organization_id,
            CRMTask.status.in_(("pending", "in_progress")),
            CRMTask.due_at.is_not(None),
            CRMTask.due_at <= soon,
        )
        if preferences.only_assigned_items:
            query = query.where(CRMTask.assigned_to_id == actor.id)
        for task in db.scalars(query):
            due = utc_value(task.due_at)
            overdue = bool(due and due < now)
            add_notification(
                db, actor, key=f"task:{task.id}:{'overdue' if overdue else 'soon'}",
                kind="task", priority="critical" if overdue else "normal",
                title="Tarefa atrasada" if overdue else "Tarefa próxima",
                message=f"{task.title} · prazo em {due.astimezone().strftime('%d/%m/%Y %H:%M') if due else 'breve'}",
                event_at=due or now, target_view="crm", target_filter="task:overdue" if overdue else "task:all",
            )

    if preferences.collections_enabled:
        due_limit = today + timedelta(days=3)
        query = select(PaymentInstallment).where(
            PaymentInstallment.organization_id == actor.organization_id,
            PaymentInstallment.status.in_(("pending", "overdue")),
            PaymentInstallment.due_date <= due_limit,
        )
        if preferences.only_assigned_items:
            query = query.where(PaymentInstallment.collection_assigned_user_id == actor.id)
        for installment in db.scalars(query):
            overdue = installment.due_date < today or installment.status == "overdue"
            add_notification(
                db, actor, key=f"installment:{installment.id}:{'overdue' if overdue else 'soon'}",
                kind="collection", priority="critical" if overdue else "high",
                title="Cobrança atrasada" if overdue else "Parcela próxima do vencimento",
                message=f"Parcela {installment.installment_number} · vencimento {installment.due_date.strftime('%d/%m/%Y')}",
                event_at=datetime.combine(installment.due_date, time.min, tzinfo=timezone.utc),
                target_view="collections", target_filter="attention:critical" if overdue else "status:due_soon",
            )

    if preferences.promises_enabled:
        query = select(CollectionAction).where(
            CollectionAction.organization_id == actor.organization_id,
            CollectionAction.outcome == "promise_to_pay",
            CollectionAction.promise_date.is_not(None),
            CollectionAction.promise_date < today,
            CollectionAction.cancelled_at.is_(None),
        )
        if preferences.only_assigned_items:
            query = query.where(CollectionAction.created_by_user_id == actor.id)
        for action in db.scalars(query):
            add_notification(
                db, actor, key=f"promise:{action.id}:overdue", kind="promise", priority="critical",
                title="Promessa de pagamento vencida",
                message=f"A promessa de {action.promise_date.strftime('%d/%m/%Y')} precisa de acompanhamento.",
                event_at=datetime.combine(action.promise_date, time.min, tzinfo=timezone.utc),
                target_view="collections", target_filter="promise:overdue",
            )

    if preferences.goals_enabled and actor.role in {"admin", "supervisor"}:
        report = build_overview(db, IdentityContext.from_entities(user=actor, organization=actor.organization), today.replace(day=1))
        for metric in report.organization_metrics:
            if metric.status == "attention" and metric.target_value > 0:
                add_notification(
                    db, actor, key=f"goal:{today:%Y-%m}:{metric.metric}:attention", kind="goal", priority="high",
                    title=f"Meta em atenção: {metric.label}",
                    message=f"A projeção atual indica {metric.projected_percent}% da meta mensal.",
                    event_at=now, target_view="performance", target_filter=metric.metric,
                )
    db.commit()


@router.get("", response_model=NotificationPage)
def list_notifications(
    notification_type: str | None = Query(default=None),
    priority: str | None = Query(default=None),
    read_status: str = Query(default="all", pattern="^(all|read|unread)$"),
    limit: int = Query(default=100, ge=1, le=200),
    db: Session = Depends(get_db), actor: User = Depends(get_current_user),
):
    synchronize_notifications(db, actor)
    filters = [Notification.organization_id == actor.organization_id, Notification.user_id == actor.id]
    if notification_type and notification_type != "all": filters.append(Notification.notification_type == notification_type)
    if priority and priority != "all": filters.append(Notification.priority == priority)
    if read_status == "read": filters.append(Notification.read_at.is_not(None))
    elif read_status == "unread": filters.append(Notification.read_at.is_(None))
    items = list(db.scalars(select(Notification).where(*filters).order_by(Notification.read_at.is_not(None), Notification.event_at.desc()).limit(limit)))
    all_scope = [Notification.organization_id == actor.organization_id, Notification.user_id == actor.id]
    return NotificationPage(
        items=items,
        total=db.scalar(select(func.count(Notification.id)).where(*filters)) or 0,
        unread_count=db.scalar(select(func.count(Notification.id)).where(*all_scope, Notification.read_at.is_(None))) or 0,
        critical_unread_count=db.scalar(select(func.count(Notification.id)).where(*all_scope, Notification.read_at.is_(None), Notification.priority == "critical")) or 0,
    )


@router.patch("/{notification_id}", response_model=NotificationRead)
def update_notification_status(notification_id: uuid.UUID, payload: NotificationStatusUpdate, db: Session = Depends(get_db), actor: User = Depends(get_current_user)):
    item = db.scalar(select(Notification).where(Notification.id == notification_id, Notification.user_id == actor.id, Notification.organization_id == actor.organization_id))
    if not item: raise HTTPException(status_code=404, detail="Notificação não encontrada")
    item.read_at = datetime.now(timezone.utc) if payload.read else None
    db.commit(); db.refresh(item); return item


@router.post("/read-all", status_code=status.HTTP_204_NO_CONTENT)
def mark_all_notifications_read(db: Session = Depends(get_db), actor: User = Depends(get_current_user)):
    db.execute(update(Notification).where(Notification.organization_id == actor.organization_id, Notification.user_id == actor.id, Notification.read_at.is_(None)).values(read_at=datetime.now(timezone.utc)))
    db.commit(); return None


@router.get("/preferences", response_model=NotificationPreferencesRead)
def read_preferences(db: Session = Depends(get_db), actor: User = Depends(get_current_user)):
    preference = get_preferences(db, actor); db.commit(); return preference


@router.put("/preferences", response_model=NotificationPreferencesRead)
def update_preferences(payload: NotificationPreferencesUpdate, db: Session = Depends(get_db), actor: User = Depends(get_current_user)):
    preference = get_preferences(db, actor)
    for field, value in payload.model_dump().items(): setattr(preference, field, value)
    record_audit(db, organization_id=actor.organization_id, user_id=actor.id, entity_type="notification_preferences", entity_id=preference.id, action="updated", new_values=payload.model_dump())
    db.commit(); db.refresh(preference); return preference
