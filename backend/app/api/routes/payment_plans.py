import uuid
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.api.deps import get_current_user
from app.core.config import settings
from app.db.session import get_db
from app.models.client import Client
from app.models.user import User
from app.schemas.payment_plan import PaymentPlanSimulationCreate, PaymentPlanSimulationRead
from app.services.payment_plan_engine import simulate

router = APIRouter()


@router.post("/{client_id}/simulate", response_model=PaymentPlanSimulationRead)
def simulate_payment_plans(
    client_id: uuid.UUID,
    payload: PaymentPlanSimulationCreate,
    db: Session = Depends(get_db),
    actor: User = Depends(get_current_user),
):
    client = db.scalar(
        select(Client)
        .where(
            Client.id == client_id,
            Client.organization_id == actor.organization_id,
            Client.archived_at.is_(None),
        )
        .options(selectinload(Client.incomes), selectinload(Client.expenses), selectinload(Client.debts))
    )
    if not client:
        raise HTTPException(status_code=404, detail="Cliente não encontrado")
    try:
        return simulate(
            client,
            payload,
            actor.organization_id,
            Decimal(str(settings.minimum_existential_reference)),
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
