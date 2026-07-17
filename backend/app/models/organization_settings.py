from __future__ import annotations
import uuid
from sqlalchemy import Boolean, ForeignKey, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base, TimestampMixin

class OrganizationSettings(TimestampMixin, Base):
    __tablename__ = "organization_settings"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    organization_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"),
        unique=True, nullable=False, index=True
    )
    timezone: Mapped[str] = mapped_column(String(80), default="America/Sao_Paulo", nullable=False)
    language: Mapped[str] = mapped_column(String(20), default="pt-BR", nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="BRL", nullable=False)
    date_format: Mapped[str] = mapped_column(String(30), default="DD/MM/YYYY", nullable=False)
    allow_client_portal: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    allow_external_integrations: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    require_mfa_for_admins: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    organization = relationship("Organization", back_populates="settings")
