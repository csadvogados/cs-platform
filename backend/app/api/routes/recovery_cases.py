from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.api.deps import require_permissions
from app.db.session import get_db
from app.models.recovery import RecoveryCaseStage, RecoveryCaseStatus
from app.schemas.recovery import (
    RecoveryCaseCreate, RecoveryCasePage, RecoveryCaseRead,
    RecoveryCaseTransition, RecoveryCaseUpdate,
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
