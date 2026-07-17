from __future__ import annotations
import uuid
from sqlalchemy import Boolean, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base, TimestampMixin
from app.models.organization_enums import OrganizationStatus, OrganizationType

class Organization(TimestampMixin, Base):
    __tablename__ = "organizations"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    legal_name: Mapped[str] = mapped_column(String(200), nullable=False)
    trade_name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    tax_id: Mapped[str | None] = mapped_column(String(20), unique=True, nullable=True)
    state_registration: Mapped[str | None] = mapped_column(String(30), nullable=True)
    municipal_registration: Mapped[str | None] = mapped_column(String(30), nullable=True)
    organization_type: Mapped[str] = mapped_column(
        String(30), default=OrganizationType.LAW_FIRM.value, nullable=False, index=True
    )
    email: Mapped[str | None] = mapped_column(String(320), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(30), nullable=True)
    website: Mapped[str | None] = mapped_column(String(255), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(
        String(30), default=OrganizationStatus.ACTIVE.value, nullable=False, index=True
    )
    is_system_default: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    users = relationship("User", back_populates="organization", cascade="all, delete-orphan")
    clients = relationship("Client", back_populates="organization", cascade="all, delete-orphan")
    settings = relationship(
        "OrganizationSettings", back_populates="organization",
        cascade="all, delete-orphan", uselist=False
    )
    branding = relationship(
        "OrganizationBranding", back_populates="organization",
        cascade="all, delete-orphan", uselist=False
    )
    license = relationship(
        "OrganizationLicense", back_populates="organization",
        cascade="all, delete-orphan", uselist=False
    )
    addresses = relationship(
        "OrganizationAddress", back_populates="organization",
        cascade="all, delete-orphan"
    )
