from __future__ import annotations
from uuid import UUID
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session
from app.core.exceptions import ConflictException, DatabaseException, ResourceNotFoundException
from app.models.organization import Organization
from app.models.organization_address import OrganizationAddress
from app.models.organization_branding import OrganizationBranding
from app.models.organization_license import OrganizationLicense
from app.models.organization_settings import OrganizationSettings
from app.repositories.organization import OrganizationRepository
from app.schemas.organization import (
    OrganizationBrandingCreate, OrganizationCreate, OrganizationLicenseCreate,
    OrganizationRead, OrganizationSettingsCreate, OrganizationUpdate
)

class OrganizationService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repository = OrganizationRepository(db)

    def get(self, organization_id: UUID) -> OrganizationRead:
        org = self.repository.get_by_id(organization_id)
        if org is None:
            raise ResourceNotFoundException(resource="Organização", resource_id=organization_id)
        return OrganizationRead.model_validate(org)

    def create(self, payload: OrganizationCreate) -> OrganizationRead:
        if payload.tax_id and self.repository.exists_by_tax_id(payload.tax_id):
            raise ConflictException(
                code="ORGANIZATION_TAX_ID_ALREADY_EXISTS",
                message="Já existe uma organização com este CNPJ."
            )
        try:
            org = Organization(
                legal_name=payload.legal_name,
                trade_name=payload.trade_name,
                tax_id=payload.tax_id,
                state_registration=payload.state_registration,
                municipal_registration=payload.municipal_registration,
                organization_type=payload.organization_type.value,
                email=str(payload.email) if payload.email else None,
                phone=payload.phone,
                website=str(payload.website) if payload.website else None,
                description=payload.description,
                status=payload.status.value,
                is_system_default=payload.is_system_default,
            )
            self.repository.add(org)

            settings = payload.settings or OrganizationSettingsCreate()
            self.repository.add(OrganizationSettings(
                organization_id=org.id, **settings.model_dump()
            ))

            branding = payload.branding or OrganizationBrandingCreate()
            self.repository.add(OrganizationBranding(
                organization_id=org.id, **branding.model_dump(mode="json")
            ))

            lic = payload.license or OrganizationLicenseCreate()
            self.repository.add(OrganizationLicense(
                organization_id=org.id,
                plan=lic.plan.value, status=lic.status.value,
                starts_at=lic.starts_at, expires_at=lic.expires_at,
                max_users=lic.max_users, max_storage_mb=lic.max_storage_mb
            ))

            for item in payload.addresses:
                data = item.model_dump()
                data["address_type"] = item.address_type.value
                self.repository.add(OrganizationAddress(organization_id=org.id, **data))

            self.db.commit()
            return self.get(org.id)
        except SQLAlchemyError as exc:
            self.db.rollback()
            raise DatabaseException("Não foi possível criar a organização.", cause=exc) from exc

    def update(self, organization_id: UUID, payload: OrganizationUpdate) -> OrganizationRead:
        org = self.repository.get_by_id(organization_id)
        if org is None:
            raise ResourceNotFoundException(resource="Organização", resource_id=organization_id)
        try:
            data = payload.model_dump(exclude_unset=True)
            for key, value in data.items():
                if key in {"organization_type", "status"} and value is not None:
                    value = value.value
                if key in {"email", "website"} and value is not None:
                    value = str(value)
                setattr(org, key, value)
            self.db.commit()
            self.db.refresh(org)
            return self.get(org.id)
        except SQLAlchemyError as exc:
            self.db.rollback()
            raise DatabaseException("Não foi possível atualizar a organização.", cause=exc) from exc
