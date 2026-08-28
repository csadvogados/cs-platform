from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session
from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.client import Client
from app.models.user import User
router=APIRouter()


def _summary(db: Session, actor: User) -> dict[str, int]:
    organization_filter = Client.organization_id == actor.organization_id
    active_filter = Client.archived_at.is_(None)
    return {
        "clients_total": db.scalar(select(func.count(Client.id)).where(organization_filter)) or 0,
        "clients_active": db.scalar(
            select(func.count(Client.id)).where(organization_filter, active_filter)
        ) or 0,
        "clients_archived": db.scalar(
            select(func.count(Client.id)).where(organization_filter, Client.archived_at.is_not(None))
        ) or 0,
        "users_active": db.scalar(
            select(func.count(User.id)).where(
                User.organization_id == actor.organization_id,
                User.status == "active",
                User.deleted_at.is_(None),
            )
        ) or 0,
    }


@router.get("/summary")
def dashboard_summary(db: Session = Depends(get_db), actor: User = Depends(get_current_user)):
    return _summary(db, actor)


@router.get("")
def dashboard(db: Session = Depends(get_db), actor: User = Depends(get_current_user)):
    return _summary(db, actor)

