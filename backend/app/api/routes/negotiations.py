from __future__ import annotations

import uuid
from datetime import datetime, timezone
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.api.deps import require_permissions
from app.core.config import settings
from app.db.session import get_db
from app.models.client import Client
from app.models.financial import Debt
from app.models.negotiation import Negotiation, NegotiationOffer
from app.models.recovery import RecoveryCase
from app.schemas.negotiation import NegotiationCreate, NegotiationOfferCreate, NegotiationOfferDecision, NegotiationOfferRead, NegotiationRead
from app.security.identity import IdentityContext
from app.security.permissions import PermissionCode
from app.services.audit import record_audit
from app.services.diagnosis_engine import calculate
from app.services.negotiation_engine import evaluate_offer

router = APIRouter()


def owned_negotiation(db: Session, organization_id: uuid.UUID, negotiation_id: uuid.UUID) -> Negotiation:
    item = db.scalar(select(Negotiation).options(selectinload(Negotiation.offers)).where(
        Negotiation.id == negotiation_id, Negotiation.organization_id == organization_id
    ))
    if not item:
        raise HTTPException(status_code=404, detail="Negociação não encontrada")
    return item


@router.post("", response_model=NegotiationRead, status_code=status.HTTP_201_CREATED)
def create_negotiation(payload: NegotiationCreate, db: Session = Depends(get_db), identity: IdentityContext = Depends(require_permissions(PermissionCode.NEGOTIATION_CREATE.value))):
    case = db.scalar(select(RecoveryCase).where(RecoveryCase.id == payload.recovery_case_id, RecoveryCase.organization_id == identity.organization_id, RecoveryCase.deleted_at.is_(None)))
    if not case:
        raise HTTPException(status_code=404, detail="Caso de recuperação não encontrado")
    debt = db.scalar(select(Debt).where(Debt.id == payload.debt_id, Debt.client_id == case.client_id, Debt.organization_id == identity.organization_id))
    if not debt:
        raise HTTPException(status_code=422, detail="A dívida não pertence ao cliente do caso")
    item = Negotiation(organization_id=identity.organization_id, recovery_case_id=case.id, client_id=case.client_id,
                       debt_id=debt.id, creditor_id=debt.creditor_id, assigned_user_id=payload.assigned_user_id or identity.user_id,
                       channel=payload.channel, external_reference=payload.external_reference, expires_at=payload.expires_at,
                       notes=payload.notes, opened_at=datetime.now(timezone.utc))
    db.add(item); db.flush()
    record_audit(db, organization_id=identity.organization_id, user_id=identity.user_id, entity_type="negotiation", entity_id=item.id,
                 action="create", new_values={"case_id": str(case.id), "debt_id": str(debt.id), "channel": item.channel})
    db.commit()
    return owned_negotiation(db, identity.organization_id, item.id)


@router.get("", response_model=list[NegotiationRead])
def list_negotiations(client_id: uuid.UUID | None = None, recovery_case_id: uuid.UUID | None = None, db: Session = Depends(get_db), identity: IdentityContext = Depends(require_permissions(PermissionCode.NEGOTIATION_READ.value))):
    query = select(Negotiation).options(selectinload(Negotiation.offers)).where(Negotiation.organization_id == identity.organization_id)
    if client_id: query = query.where(Negotiation.client_id == client_id)
    if recovery_case_id: query = query.where(Negotiation.recovery_case_id == recovery_case_id)
    return list(db.scalars(query.order_by(Negotiation.updated_at.desc())))


@router.get("/{negotiation_id}", response_model=NegotiationRead)
def get_negotiation(negotiation_id: uuid.UUID, db: Session = Depends(get_db), identity: IdentityContext = Depends(require_permissions(PermissionCode.NEGOTIATION_READ.value))):
    return owned_negotiation(db, identity.organization_id, negotiation_id)


@router.post("/{negotiation_id}/offers", response_model=NegotiationOfferRead, status_code=status.HTTP_201_CREATED)
def create_offer(negotiation_id: uuid.UUID, payload: NegotiationOfferCreate, db: Session = Depends(get_db), identity: IdentityContext = Depends(require_permissions(PermissionCode.NEGOTIATION_UPDATE.value))):
    negotiation = owned_negotiation(db, identity.organization_id, negotiation_id)
    if negotiation.status != "open":
        raise HTTPException(status_code=409, detail="A negociação não está aberta")
    client = db.scalar(select(Client).options(selectinload(Client.incomes), selectinload(Client.expenses), selectinload(Client.debts)).where(Client.id == negotiation.client_id, Client.organization_id == identity.organization_id))
    debt = db.get(Debt, negotiation.debt_id)
    diagnosis = calculate(client, Decimal(str(settings.minimum_existential_reference)))
    assessment = evaluate_offer(debt_amount=debt.current_balance, offered_amount=payload.offered_amount,
                                installment_amount=payload.installment_amount, down_payment=payload.down_payment,
                                payment_capacity=diagnosis["max_payment_capacity"], data_quality_score=diagnosis["data_quality_score"])
    sequence = (db.scalar(select(func.max(NegotiationOffer.sequence_number)).where(NegotiationOffer.negotiation_id == negotiation.id)) or 0) + 1
    offer = NegotiationOffer(organization_id=identity.organization_id, negotiation_id=negotiation.id, created_by_user_id=identity.user_id,
                             sequence_number=sequence, original_amount=debt.current_balance, **payload.model_dump(), **assessment)
    db.add(offer); negotiation.version += 1; db.flush()
    record_audit(db, organization_id=identity.organization_id, user_id=identity.user_id, entity_type="negotiation_offer", entity_id=offer.id,
                 action="create", new_values={"negotiation_id": str(negotiation.id), "sequence": sequence, "decision": offer.engine_decision, "score": offer.engine_score})
    db.commit(); db.refresh(offer)
    return offer


@router.post("/{negotiation_id}/offers/{offer_id}/decision", response_model=NegotiationRead)
def decide_offer(negotiation_id: uuid.UUID, offer_id: uuid.UUID, payload: NegotiationOfferDecision, db: Session = Depends(get_db), identity: IdentityContext = Depends(require_permissions(PermissionCode.NEGOTIATION_APPROVE.value))):
    negotiation = owned_negotiation(db, identity.organization_id, negotiation_id)
    offer = next((item for item in negotiation.offers if item.id == offer_id), None)
    if not offer:
        raise HTTPException(status_code=404, detail="Proposta não encontrada")
    if offer.status != "pending":
        raise HTTPException(status_code=409, detail="A proposta já foi decidida")
    offer.status = payload.status; offer.responded_at = datetime.now(timezone.utc); negotiation.version += 1
    if payload.status == "accepted":
        negotiation.status = "accepted"; negotiation.closed_at = offer.responded_at; negotiation.closure_reason = payload.reason or "Proposta aceita"
        for other in negotiation.offers:
            if other.id != offer.id and other.status == "pending": other.status = "withdrawn"; other.responded_at = offer.responded_at
    record_audit(db, organization_id=identity.organization_id, user_id=identity.user_id, entity_type="negotiation_offer", entity_id=offer.id,
                 action="decision", new_values={"status": offer.status, "reason": payload.reason})
    db.commit()
    return owned_negotiation(db, identity.organization_id, negotiation.id)
