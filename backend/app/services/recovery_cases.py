from __future__ import annotations

import math
import uuid
from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.client import Client
from app.models.document import ClientDocument
from app.models.financial import Diagnosis
from app.models.recovery import RecoveryCase, RecoveryCaseStage, RecoveryCaseStatus
from app.models.user import User
from app.schemas.recovery import RecoveryCaseCreate, RecoveryCaseTransition, RecoveryCaseUpdate


ALLOWED_TRANSITIONS: dict[str, set[str]] = {
    RecoveryCaseStatus.DRAFT.value: {RecoveryCaseStatus.ACTIVE.value, RecoveryCaseStatus.CANCELLED.value},
    RecoveryCaseStatus.ACTIVE.value: {
        RecoveryCaseStatus.ON_HOLD.value, RecoveryCaseStatus.RESOLVED.value,
        RecoveryCaseStatus.JUDICIALIZED.value, RecoveryCaseStatus.CANCELLED.value,
    },
    RecoveryCaseStatus.ON_HOLD.value: {RecoveryCaseStatus.ACTIVE.value, RecoveryCaseStatus.CANCELLED.value},
    RecoveryCaseStatus.RESOLVED.value: {RecoveryCaseStatus.ARCHIVED.value},
    RecoveryCaseStatus.JUDICIALIZED.value: {RecoveryCaseStatus.ARCHIVED.value},
    RecoveryCaseStatus.CANCELLED.value: {RecoveryCaseStatus.ARCHIVED.value},
    RecoveryCaseStatus.ARCHIVED.value: set(),
}

TERMINAL_STATUSES = {
    RecoveryCaseStatus.RESOLVED.value, RecoveryCaseStatus.JUDICIALIZED.value,
    RecoveryCaseStatus.CANCELLED.value, RecoveryCaseStatus.ARCHIVED.value,
}

NEXT_STAGES = {
    RecoveryCaseStage.INTAKE.value: RecoveryCaseStage.DOCUMENTS.value,
    RecoveryCaseStage.DOCUMENTS.value: RecoveryCaseStage.DIAGNOSIS.value,
    RecoveryCaseStage.DIAGNOSIS.value: RecoveryCaseStage.PLANNING.value,
    RecoveryCaseStage.PLANNING.value: RecoveryCaseStage.NEGOTIATION.value,
    RecoveryCaseStage.NEGOTIATION.value: RecoveryCaseStage.JUDICIAL_PREPARATION.value,
}
REQUIRED_JUDICIAL_DOCUMENTS = {"identification", "income_proof", "residence_proof", "debt_statement"}


def _client(db: Session, organization_id: uuid.UUID, client_id: uuid.UUID) -> Client:
    client = db.scalar(select(Client).where(Client.id == client_id, Client.organization_id == organization_id))
    if client is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Cliente não encontrado")
    return client


def _assignee(db: Session, organization_id: uuid.UUID, user_id: uuid.UUID | None) -> User | None:
    if user_id is None:
        return None
    user = db.scalar(select(User).where(
        User.id == user_id, User.organization_id == organization_id,
        User.status == "active", User.deleted_at.is_(None),
    ))
    if user is None:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "Responsável inválido")
    return user


def get_case(db: Session, organization_id: uuid.UUID, case_id: uuid.UUID) -> RecoveryCase:
    case = db.scalar(select(RecoveryCase).where(
        RecoveryCase.id == case_id, RecoveryCase.organization_id == organization_id,
        RecoveryCase.deleted_at.is_(None),
    ))
    if case is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Caso de recuperação não encontrado")
    return case


def create_case(db: Session, organization_id: uuid.UUID, payload: RecoveryCaseCreate) -> RecoveryCase:
    _client(db, organization_id, payload.client_id)
    _assignee(db, organization_id, payload.assigned_user_id)
    identifier = uuid.uuid4()
    case = RecoveryCase(
        id=identifier, organization_id=organization_id, client_id=payload.client_id,
        case_number=f"REC-{datetime.now(timezone.utc):%Y%m}-{identifier.hex[:8].upper()}",
        source=payload.source.value, assigned_user_id=payload.assigned_user_id, notes=payload.notes,
    )
    db.add(case)
    db.flush()
    return case


def list_cases(db: Session, organization_id: uuid.UUID, *, page: int, page_size: int,
               case_status: RecoveryCaseStatus | None = None,
               stage: RecoveryCaseStage | None = None, client_id: uuid.UUID | None = None):
    filters = [RecoveryCase.organization_id == organization_id, RecoveryCase.deleted_at.is_(None)]
    if case_status:
        filters.append(RecoveryCase.status == case_status.value)
    if stage:
        filters.append(RecoveryCase.stage == stage.value)
    if client_id:
        filters.append(RecoveryCase.client_id == client_id)
    total = db.scalar(select(func.count()).select_from(RecoveryCase).where(*filters)) or 0
    items = list(db.scalars(
        select(RecoveryCase).where(*filters).order_by(RecoveryCase.updated_at.desc())
        .offset((page - 1) * page_size).limit(page_size)
    ))
    return items, total, math.ceil(total / page_size) if total else 0


def update_case(db: Session, case: RecoveryCase, payload: RecoveryCaseUpdate) -> RecoveryCase:
    if case.version != payload.version:
        raise HTTPException(status.HTTP_409_CONFLICT, "Caso alterado por outro usuário; recarregue e tente novamente")
    fields = payload.model_fields_set
    if "assigned_user_id" in fields:
        _assignee(db, case.organization_id, payload.assigned_user_id)
        case.assigned_user_id = payload.assigned_user_id
    if "notes" in fields:
        case.notes = payload.notes
    if "stage" in fields and payload.stage is not None:
        expected = NEXT_STAGES.get(case.stage)
        if payload.stage.value != expected:
            raise HTTPException(status.HTTP_409_CONFLICT, f"Avanço de etapa inválido: {case.stage} -> {payload.stage.value}")
        case.stage = payload.stage.value
    case.version += 1
    db.flush()
    return case


def transition_case(db: Session, case: RecoveryCase, payload: RecoveryCaseTransition) -> RecoveryCase:
    if case.version != payload.version:
        raise HTTPException(status.HTTP_409_CONFLICT, "Caso alterado por outro usuário; recarregue e tente novamente")
    target = payload.status.value
    if target not in ALLOWED_TRANSITIONS.get(case.status, set()):
        raise HTTPException(status.HTTP_409_CONFLICT, f"Transição inválida: {case.status} -> {target}")
    if target in {RecoveryCaseStatus.CANCELLED.value, RecoveryCaseStatus.ARCHIVED.value} and not payload.reason:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "Motivo obrigatório para esta transição")
    if target == RecoveryCaseStatus.JUDICIALIZED.value:
        if case.stage != RecoveryCaseStage.JUDICIAL_PREPARATION.value:
            raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "O caso deve estar na etapa de preparação judicial")
        validated = set(db.scalars(select(ClientDocument.category).where(
            ClientDocument.client_id == case.client_id,
            ClientDocument.organization_id == case.organization_id,
            ClientDocument.status == "validated",
            ClientDocument.deleted_at.is_(None),
        )))
        missing = REQUIRED_JUDICIAL_DOCUMENTS - validated
        if missing:
            raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "O dossiê judicial possui documentos obrigatórios pendentes")
        diagnosis = db.scalar(select(Diagnosis.id).where(
            Diagnosis.client_id == case.client_id,
            Diagnosis.organization_id == case.organization_id,
        ).limit(1))
        if diagnosis is None:
            raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "Salve um diagnóstico antes de judicializar o caso")
    now = datetime.now(timezone.utc)
    case.status = target
    if payload.stage is not None:
        case.stage = payload.stage.value
    elif target == RecoveryCaseStatus.ACTIVE.value and case.stage == RecoveryCaseStage.CLOSED.value:
        case.stage = RecoveryCaseStage.INTAKE.value
    elif target in TERMINAL_STATUSES:
        case.stage = RecoveryCaseStage.CLOSED.value
    if target == RecoveryCaseStatus.ACTIVE.value and case.opened_at is None:
        case.opened_at = now
    if target in TERMINAL_STATUSES:
        case.closed_at = now
        case.closure_reason = payload.reason
    case.version += 1
    db.flush()
    return case
