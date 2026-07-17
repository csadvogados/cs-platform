from __future__ import annotations
from datetime import datetime
import uuid
from sqlalchemy import DateTime, ForeignKey, Integer, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base, TimestampMixin
from app.models.organization_enums import LicenseStatus, OrganizationPlan

class OrganizationLicense(TimestampMixin, Base):
    __tablename__ = "organization_licenses"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    organization_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"),
        unique=True, nullable=False, index=True
    )
    plan: Mapped[str] = mapped_column(
        String(30), default=OrganizationPlan.STARTER.value, nullable=False, index=True
    )
    status: Mapped[str] = mapped_column(
        String(30), default=LicenseStatus.TRIAL.value, nullable=False, index=True
    )
    starts_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    max_users: Mapped[int] = mapped_column(Integer, default=5, nullable=False)
    max_storage_mb: Mapped[int] = mapped_column(Integer, default=1024, nullable=False)

    organization = relationship("Organization", back_populates="license")
