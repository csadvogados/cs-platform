from __future__ import annotations
from uuid import UUID
from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload
from app.models.organization import Organization

class OrganizationRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_by_id(self, organization_id: UUID) -> Organization | None:
        return self.db.scalar(
            select(Organization)
            .options(
                selectinload(Organization.settings),
                selectinload(Organization.branding),
                selectinload(Organization.license),
                selectinload(Organization.addresses),
            )
            .where(Organization.id == organization_id)
        )

    def exists_by_tax_id(self, tax_id: str, exclude_id: UUID | None = None) -> bool:
        query = select(func.count()).select_from(Organization).where(
            Organization.tax_id == tax_id
        )
        if exclude_id:
            query = query.where(Organization.id != exclude_id)
        return bool(self.db.scalar(query))

    def add(self, instance):
        self.db.add(instance)
        self.db.flush()
        return instance
