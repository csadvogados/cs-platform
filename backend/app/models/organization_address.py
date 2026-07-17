from __future__ import annotations
import uuid
from sqlalchemy import Boolean, ForeignKey, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base, TimestampMixin
from app.models.organization_enums import AddressType

class OrganizationAddress(TimestampMixin, Base):
    __tablename__ = "organization_addresses"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    organization_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False, index=True
    )
    address_type: Mapped[str] = mapped_column(
        String(30), default=AddressType.HEADQUARTERS.value, nullable=False, index=True
    )
    postal_code: Mapped[str | None] = mapped_column(String(12), nullable=True)
    street: Mapped[str | None] = mapped_column(String(255), nullable=True)
    number: Mapped[str | None] = mapped_column(String(30), nullable=True)
    complement: Mapped[str | None] = mapped_column(String(120), nullable=True)
    district: Mapped[str | None] = mapped_column(String(120), nullable=True)
    city: Mapped[str | None] = mapped_column(String(120), nullable=True)
    state: Mapped[str | None] = mapped_column(String(2), nullable=True)
    country: Mapped[str] = mapped_column(String(2), default="BR", nullable=False)
    is_primary: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    organization = relationship("Organization", back_populates="addresses")
