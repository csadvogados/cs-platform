from __future__ import annotations

import uuid
from datetime import date, datetime

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Index, Integer, Numeric, String, Text, UniqueConstraint, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin


class Negotiation(TimestampMixin, Base):
    __tablename__ = "negotiations"
    __table_args__ = (
        Index("ix_negotiations_org_status_updated", "organization_id", "status", "updated_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    organization_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    recovery_case_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("recovery_cases.id", ondelete="CASCADE"), nullable=False, index=True)
    client_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("clients.id", ondelete="CASCADE"), nullable=False, index=True)
    debt_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("debts.id", ondelete="RESTRICT"), nullable=False, index=True)
    creditor_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("creditors.id", ondelete="SET NULL"), nullable=True, index=True)
    assigned_user_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    status: Mapped[str] = mapped_column(String(24), nullable=False, default="open", index=True)
    channel: Mapped[str] = mapped_column(String(24), nullable=False, default="other")
    external_reference: Mapped[str | None] = mapped_column(String(120), nullable=True)
    opened_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, index=True)
    closed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    closure_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1, server_default="1")

    offers = relationship("NegotiationOffer", back_populates="negotiation", cascade="all, delete-orphan", order_by="NegotiationOffer.created_at")


class NegotiationOffer(TimestampMixin, Base):
    __tablename__ = "negotiation_offers"
    __table_args__ = (
        UniqueConstraint("negotiation_id", "sequence_number", name="uq_negotiation_offers_sequence"),
        Index("ix_negotiation_offers_org_decision_created", "organization_id", "engine_decision", "created_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    organization_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    negotiation_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("negotiations.id", ondelete="CASCADE"), nullable=False, index=True)
    created_by_user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True)
    sequence_number: Mapped[int] = mapped_column(Integer, nullable=False)
    origin: Mapped[str] = mapped_column(String(20), nullable=False)
    original_amount: Mapped[float] = mapped_column(Numeric(14, 2), nullable=False)
    offered_amount: Mapped[float] = mapped_column(Numeric(14, 2), nullable=False)
    down_payment: Mapped[float] = mapped_column(Numeric(14, 2), nullable=False, default=0)
    installment_count: Mapped[int] = mapped_column(Integer, nullable=False)
    installment_amount: Mapped[float] = mapped_column(Numeric(14, 2), nullable=False)
    annual_interest_rate: Mapped[float] = mapped_column(Numeric(7, 4), nullable=False, default=0)
    first_due_date: Mapped[date] = mapped_column(Date, nullable=False)
    valid_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    sustainable: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, index=True)
    capacity_usage_percentage: Mapped[float] = mapped_column(Numeric(7, 2), nullable=False, default=0)
    engine_score: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    engine_decision: Mapped[str] = mapped_column(String(24), nullable=False, index=True)
    engine_reason: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(24), nullable=False, default="pending", index=True)
    responded_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    negotiation = relationship("Negotiation", back_populates="offers")


__all__ = ["Negotiation", "NegotiationOffer"]
