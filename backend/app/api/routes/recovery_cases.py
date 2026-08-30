from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Query, status
from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.api.deps import require_permissions
from app.db.session import get_db
from app.models.recovery import JudicialProcess, JudicialProcessEvent, RecoveryCaseStage, RecoveryCaseStatus
from app.schemas.recovery import (
    RecoveryCaseCreate, RecoveryCasePage, RecoveryCaseRead,
    RecoveryCaseTransition, RecoveryCaseUpdate,
    JudicialDeadlineComplete, JudicialProcessEventCreate, JudicialProcessEventRead, JudicialProcessRead, JudicialProcessUpsert,
)
from app.security.identity import IdentityContext
from app.security.permissions import PermissionCode
from app.services.audit import record_audit
from app.services.recovery_cases import create_case, get_case, list_cases, transition_case, update_case


router = APIRouter()


@router.post("", response_model=RecoveryCaseRead, status_code=status.HTTP_201_CREATED)
def create_recovery_case(
    payload: RecoveryCaseCreate,
    db: Session = Depends(get_db),
    identity: IdentityContext = Depends(require_permissions(PermissionCode.RECOVERY_CASE_CREATE.value)),
):
    case = create_case(db, identity.organization_id, payload)
    record_audit(db, organization_id=identity.organization_id, user_id=identity.user_id,
                 entity_type="recovery_case", entity_id=case.id, action="create",
                 new_values={"case_number": case.case_number, "client_id": str(case.client_id)})
    db.commit(); db.refresh(case)
    return case


@router.get("", response_model=RecoveryCasePage)
def get_recovery_cases(
    page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100),
    case_status: RecoveryCaseStatus | None = Query(None, alias="status"),
    stage: RecoveryCaseStage | None = None, client_id: uuid.UUID | None = None,
    db: Session = Depends(get_db),
    identity: IdentityContext = Depends(require_permissions(PermissionCode.RECOVERY_CASE_READ.value)),
):
    items, total, pages = list_cases(db, identity.organization_id, page=page, page_size=page_size,
                                     case_status=case_status, stage=stage, client_id=client_id)
    return RecoveryCasePage(items=items, total=total, page=page, page_size=page_size, pages=pages)


@router.get("/{case_id}", response_model=RecoveryCaseRead)
def get_recovery_case(
    case_id: uuid.UUID, db: Session = Depends(get_db),
    identity: IdentityContext = Depends(require_permissions(PermissionCode.RECOVERY_CASE_READ.value)),
):
    return get_case(db, identity.organization_id, case_id)


@router.patch("/{case_id}", response_model=RecoveryCaseRead)
def patch_recovery_case(
    case_id: uuid.UUID, payload: RecoveryCaseUpdate, db: Session = Depends(get_db),
    identity: IdentityContext = Depends(require_permissions(PermissionCode.RECOVERY_CASE_UPDATE.value)),
):
    case = get_case(db, identity.organization_id, case_id)
    before = {"assigned_user_id": str(case.assigned_user_id) if case.assigned_user_id else None, "version": case.version}
    update_case(db, case, payload)
    record_audit(db, organization_id=identity.organization_id, user_id=identity.user_id,
                 entity_type="recovery_case", entity_id=case.id, action="update",
                 new_values={"before": before, "version": case.version})
    db.commit(); db.refresh(case)
    return case


@router.post("/{case_id}/transitions", response_model=RecoveryCaseRead)
def post_recovery_case_transition(
    case_id: uuid.UUID, payload: RecoveryCaseTransition, db: Session = Depends(get_db),
    identity: IdentityContext = Depends(require_permissions(PermissionCode.RECOVERY_CASE_TRANSITION.value)),
):
    case = get_case(db, identity.organization_id, case_id)
    previous = {"status": case.status, "stage": case.stage, "version": case.version}
    transition_case(db, case, payload)
    record_audit(db, organization_id=identity.organization_id, user_id=identity.user_id,
                 entity_type="recovery_case", entity_id=case.id, action="transition",
                 new_values={"before": previous, "status": case.status, "stage": case.stage,
                             "reason": payload.reason, "version": case.version})
    db.commit(); db.refresh(case)
    return case


def _judicial_process(db: Session, organization_id: uuid.UUID, case_id: uuid.UUID) -> JudicialProcess:
    process = db.scalar(select(JudicialProcess).options(selectinload(JudicialProcess.events)).where(
        JudicialProcess.recovery_case_id == case_id,
        JudicialProcess.organization_id == organization_id,
    ).execution_options(populate_existing=True))
    if process is None:
        raise HTTPException(status_code=404, detail="Processo judicial não cadastrado")
    return process


@router.get("/{case_id}/judicial-process", response_model=JudicialProcessRead)
def get_judicial_process(case_id: uuid.UUID, db: Session = Depends(get_db),
                         identity: IdentityContext = Depends(require_permissions(PermissionCode.RECOVERY_CASE_READ.value))):
    get_case(db, identity.organization_id, case_id)
    return _judicial_process(db, identity.organization_id, case_id)


@router.put("/{case_id}/judicial-process", response_model=JudicialProcessRead)
def upsert_judicial_process(case_id: uuid.UUID, payload: JudicialProcessUpsert, db: Session = Depends(get_db),
                            identity: IdentityContext = Depends(require_permissions(PermissionCode.RECOVERY_CASE_UPDATE.value))):
    case = get_case(db, identity.organization_id, case_id)
    if case.status != RecoveryCaseStatus.JUDICIALIZED.value:
        raise HTTPException(status_code=422, detail="O caso precisa estar judicializado")
    process = db.scalar(select(JudicialProcess).where(
        JudicialProcess.recovery_case_id == case.id, JudicialProcess.organization_id == identity.organization_id))
    duplicate = db.scalar(select(JudicialProcess.id).where(
        JudicialProcess.organization_id == identity.organization_id,
        JudicialProcess.process_number == payload.process_number,
        JudicialProcess.recovery_case_id != case.id,
    ))
    if duplicate is not None:
        raise HTTPException(status_code=409, detail="Número de processo já cadastrado nesta organização")
    values = payload.model_dump(exclude={"version"})
    if process is None:
        if payload.version is not None:
            raise HTTPException(status_code=409, detail="O processo ainda não existe; recarregue a página")
        process = JudicialProcess(organization_id=identity.organization_id, recovery_case_id=case.id, **values)
        db.add(process)
        action = "create"
    else:
        if payload.version != process.version:
            raise HTTPException(status_code=409, detail="Processo alterado por outro usuário; recarregue e tente novamente")
        for field, value in values.items():
            setattr(process, field, value)
        process.version += 1
        action = "update"
    db.flush()
    record_audit(db, organization_id=identity.organization_id, user_id=identity.user_id,
                 entity_type="judicial_process", entity_id=process.id, action=action,
                 new_values={"case_id": str(case.id), "process_number": process.process_number, "status": process.status})
    db.commit()
    return _judicial_process(db, identity.organization_id, case.id)


@router.post("/{case_id}/judicial-process/events", response_model=JudicialProcessEventRead, status_code=status.HTTP_201_CREATED)
def create_judicial_process_event(case_id: uuid.UUID, payload: JudicialProcessEventCreate, db: Session = Depends(get_db),
                                  identity: IdentityContext = Depends(require_permissions(PermissionCode.RECOVERY_CASE_UPDATE.value))):
    get_case(db, identity.organization_id, case_id)
    process = _judicial_process(db, identity.organization_id, case_id)
    event = JudicialProcessEvent(organization_id=identity.organization_id, judicial_process_id=process.id,
                                 created_by_user_id=identity.user_id, **payload.model_dump())
    db.add(event); db.flush()
    record_audit(db, organization_id=identity.organization_id, user_id=identity.user_id,
                 entity_type="judicial_process_event", entity_id=event.id, action="create",
                 new_values={"process_id": str(process.id), "event_type": event.event_type, "title": event.title})
    db.commit(); db.refresh(event)
    return event


@router.post("/{case_id}/judicial-process/deadline/complete", response_model=JudicialProcessRead)
def complete_judicial_deadline(case_id: uuid.UUID, payload: JudicialDeadlineComplete, db: Session = Depends(get_db),
                               identity: IdentityContext = Depends(require_permissions(PermissionCode.RECOVERY_CASE_UPDATE.value))):
    get_case(db, identity.organization_id, case_id)
    process = _judicial_process(db, identity.organization_id, case_id)
    if process.version != payload.version:
        raise HTTPException(status_code=409, detail="Processo alterado por outro usuário; recarregue e tente novamente")
    if process.next_deadline is None:
        raise HTTPException(status_code=409, detail="O processo não possui prazo pendente")
    previous_deadline = process.next_deadline
    event = JudicialProcessEvent(
        organization_id=identity.organization_id, judicial_process_id=process.id,
        created_by_user_id=identity.user_id, event_date=payload.completed_at,
        event_type="deadline", title="Prazo judicial concluído",
        description=payload.notes or f"Prazo previsto para {previous_deadline:%d/%m/%Y %H:%M} concluído.",
    )
    db.add(event)
    process.next_deadline = None
    process.version += 1
    db.flush()
    record_audit(db, organization_id=identity.organization_id, user_id=identity.user_id,
                 entity_type="judicial_process", entity_id=process.id, action="deadline_complete",
                 new_values={"case_id": str(case_id), "previous_deadline": previous_deadline.isoformat(),
                             "completed_at": payload.completed_at.isoformat()})
    db.commit()
    return _judicial_process(db, identity.organization_id, case_id)
