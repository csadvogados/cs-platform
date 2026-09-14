from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_identity_context, require_superuser
from app.db.session import get_db
from app.schemas.organization import OrganizationCreate, OrganizationRead, OrganizationUpdate
from app.security.identity import IdentityContext
from app.security.permissions import PermissionCode
from app.security.rbac import RolePermissionRegistry
from app.services.organization import OrganizationService


router = APIRouter()


def _ensure_organization_access(
    identity: IdentityContext,
    organization_id: UUID,
) -> None:
    if not identity.can_access_organization(organization_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acesso negado aos dados desta organização",
        )


@router.get("/current", response_model=OrganizationRead)
def get_current_organization(
    db: Session = Depends(get_db),
    identity: IdentityContext = Depends(get_identity_context),
):
    return OrganizationService(db).get(identity.organization_id)


@router.get("/{organization_id}", response_model=OrganizationRead)
def get_organization(
    organization_id: UUID,
    db: Session = Depends(get_db),
    identity: IdentityContext = Depends(get_identity_context),
):
    _ensure_organization_access(identity, organization_id)
    return OrganizationService(db).get(organization_id)


@router.post("", response_model=OrganizationRead, status_code=status.HTTP_201_CREATED)
def create_organization(
    payload: OrganizationCreate,
    db: Session = Depends(get_db),
    _: IdentityContext = Depends(require_superuser),
):
    return OrganizationService(db).create(payload)


@router.patch("/{organization_id}", response_model=OrganizationRead)
def update_organization(
    organization_id: UUID,
    payload: OrganizationUpdate,
    db: Session = Depends(get_db),
    identity: IdentityContext = Depends(get_identity_context),
):
    _ensure_organization_access(identity, organization_id)
    can_update = identity.is_superuser or RolePermissionRegistry.has_permission(
        identity.role,
        PermissionCode.ORGANIZATION_UPDATE,
    )
    if not can_update:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Permissão insuficiente para alterar a organização",
        )
    if not identity.is_superuser and payload.is_system_default is not None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Somente superadministrador pode alterar a organização padrão",
        )
    return OrganizationService(db).update(organization_id, payload)
