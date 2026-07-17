from uuid import UUID
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from app.core.dependencies import get_database_session
from app.core.pagination import Page, PaginationParams
from app.schemas.organization import OrganizationCreate, OrganizationRead, OrganizationUpdate
from app.services.organization import OrganizationService

router = APIRouter()

@router.get("/{organization_id}", response_model=OrganizationRead)
def get_organization(
    organization_id: UUID,
    db: Session = Depends(get_database_session),
):
    return OrganizationService(db).get(organization_id)

@router.post("", response_model=OrganizationRead, status_code=status.HTTP_201_CREATED)
def create_organization(
    payload: OrganizationCreate,
    db: Session = Depends(get_database_session),
):
    return OrganizationService(db).create(payload)

@router.patch("/{organization_id}", response_model=OrganizationRead)
def update_organization(
    organization_id: UUID,
    payload: OrganizationUpdate,
    db: Session = Depends(get_database_session),
):
    return OrganizationService(db).update(organization_id, payload)
