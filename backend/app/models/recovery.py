from __future__ import annotations

import uuid
from datetime import datetime
from enum import StrEnum

from sqlalchemy import DateTime, ForeignKey, Index, Integer, String, Text, UniqueConstraint, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin


class RecoveryCaseStatus(StrEnum):
    DRAFT = "draft"
    ACTIVE = "active"
    ON_HOLD = "on_hold"
    RESOLVED = "resolved"
    JUDICIALIZED = "judicialized"
    CANCELLED = "cancelled"
    ARCHIVED = "archived"


class RecoveryCaseStage(StrEnum):
    INTAKE = "intake"
    DOCUMENTS = "documents"
    DIAGNOSIS = "diagnosis"
    PLANNING = "planning"
    NEGOTIATION = "negotiation"
    AGREEMENT_MONITORING = "agreement_monitoring"
    JUDICIAL_PREPARATION = "judicial_preparation"
    CLOSED = "closed"


class RecoveryCaseSource(StrEnum):
    MANUAL = "manual"
    IMPORT = "import"
    LEGACY = "legacy"
    API = "api"


class RecoveryCase(TimestampMixin, Base):
    __tablename__ = "recovery_cases"
    __table_args__ = (
        UniqueConstraint("organization_id", "case_number", name="uq_recovery_cases_org_number"),
        Index("ix_recovery_cases_org_status_updated", "organization_id", "status", "updated_at"),
        Index("ix_recovery_cases_org_assignee_stage", "organization_id", "assigned_user_id", "stage"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    organization_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    client_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("clients.id", ondelete="CASCADE"), nullable=False, index=True
    )
    case_number: Mapped[str] = mapped_column(String(32), nullable=False)
    status: Mapped[str] = mapped_column(String(24), nullable=False, default=RecoveryCaseStatus.DRAFT.value, index=True)
    stage: Mapped[str] = mapped_column(String(32), nullable=False, default=RecoveryCaseStage.INTAKE.value, index=True)
    source: Mapped[str] = mapped_column(String(24), nullable=False, default=RecoveryCaseSource.MANUAL.value)
    assigned_user_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )
    opened_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    closed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    closure_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1, server_default="1")
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, index=True)

    client = relationship("Client", back_populates="recovery_cases")
    assigned_user = relationship("User", foreign_keys=[assigned_user_id])
    judicial_process = relationship("JudicialProcess", back_populates="recovery_case", uselist=False, cascade="all, delete-orphan")


class JudicialProcess(TimestampMixin, Base):
    __tablename__ = "judicial_processes"
    __table_args__ = (
        UniqueConstraint("recovery_case_id", name="uq_judicial_processes_recovery_case"),
        UniqueConstraint("organization_id", "process_number", name="uq_judicial_processes_org_number"),
        Index("ix_judicial_processes_org_status_updated", "organization_id", "status", "updated_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    organization_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    recovery_case_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("recovery_cases.id", ondelete="CASCADE"), nullable=False, index=True)
    process_number: Mapped[str] = mapped_column(String(40), nullable=False)
    court: Mapped[str] = mapped_column(String(160), nullable=False)
    district: Mapped[str | None] = mapped_column(String(160), nullable=True)
    division: Mapped[str | None] = mapped_column(String(160), nullable=True)
    filed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="filed", index=True)
    next_deadline: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, index=True)
    outcome: Mapped[str | None] = mapped_column(String(32), nullable=True)
    closed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    closure_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1, server_default="1")

    recovery_case = relationship("RecoveryCase", back_populates="judicial_process")
    events = relationship("JudicialProcessEvent", back_populates="judicial_process", cascade="all, delete-orphan", order_by="JudicialProcessEvent.event_date.desc()")


class JudicialProcessEvent(TimestampMixin, Base):
    __tablename__ = "judicial_process_events"
    __table_args__ = (Index("ix_judicial_process_events_org_process_date", "organization_id", "judicial_process_id", "event_date"),)

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    organization_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    judicial_process_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("judicial_processes.id", ondelete="CASCADE"), nullable=False, index=True)
    created_by_user_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    event_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    event_type: Mapped[str] = mapped_column(String(32), nullable=False)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    judicial_process = relationship("JudicialProcess", back_populates="events")


__all__ = [
    "RecoveryCase", "RecoveryCaseSource", "RecoveryCaseStage", "RecoveryCaseStatus",
    "JudicialProcess", "JudicialProcessEvent"
]
