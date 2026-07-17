from __future__ import annotations
import uuid
from sqlalchemy import ForeignKey, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base, TimestampMixin

class OrganizationBranding(TimestampMixin, Base):
    __tablename__ = "organization_branding"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    organization_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"),
        unique=True, nullable=False, index=True
    )
    public_name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    logo_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    favicon_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    primary_color: Mapped[str] = mapped_column(String(20), default="#0F172A", nullable=False)
    secondary_color: Mapped[str] = mapped_column(String(20), default="#2563EB", nullable=False)

    organization = relationship("Organization", back_populates="branding")
