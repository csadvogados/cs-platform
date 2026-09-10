from __future__ import annotations
from datetime import date, datetime
import uuid
from sqlalchemy import Boolean, Date, DateTime, Float, ForeignKey, Integer, Numeric, String, Text, Uuid, Index, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base, TimestampMixin

class CRMContact(TimestampMixin, Base):
    __tablename__='crm_contacts'
    id: Mapped[uuid.UUID]=mapped_column(Uuid,primary_key=True,default=uuid.uuid4)
    organization_id: Mapped[uuid.UUID]=mapped_column(ForeignKey('organizations.id',ondelete='CASCADE'),index=True)
    client_id: Mapped[uuid.UUID|None]=mapped_column(ForeignKey('clients.id',ondelete='CASCADE'),index=True)
    name: Mapped[str]=mapped_column(String(200),nullable=False,index=True)
    email: Mapped[str|None]=mapped_column(String(320),index=True)
    phone: Mapped[str|None]=mapped_column(String(40),index=True)
    position: Mapped[str|None]=mapped_column(String(120))
    notes: Mapped[str|None]=mapped_column(Text)

class CRMInteraction(TimestampMixin, Base):
    __tablename__='crm_interactions'
    id: Mapped[uuid.UUID]=mapped_column(Uuid,primary_key=True,default=uuid.uuid4)
    organization_id: Mapped[uuid.UUID]=mapped_column(ForeignKey('organizations.id',ondelete='CASCADE'),index=True)
    client_id: Mapped[uuid.UUID]=mapped_column(ForeignKey('clients.id',ondelete='CASCADE'),index=True)
    user_id: Mapped[uuid.UUID|None]=mapped_column(ForeignKey('users.id',ondelete='SET NULL'),index=True)
    interaction_type: Mapped[str]=mapped_column(String(50),nullable=False,index=True)
    subject: Mapped[str]=mapped_column(String(200),nullable=False)
    description: Mapped[str|None]=mapped_column(Text)
    occurred_at: Mapped[datetime]=mapped_column(DateTime(timezone=True),nullable=False,index=True)

class CRMOpportunity(TimestampMixin, Base):
    __tablename__='crm_opportunities'
    id: Mapped[uuid.UUID]=mapped_column(Uuid,primary_key=True,default=uuid.uuid4)
    organization_id: Mapped[uuid.UUID]=mapped_column(ForeignKey('organizations.id',ondelete='CASCADE'),index=True)
    client_id: Mapped[uuid.UUID]=mapped_column(ForeignKey('clients.id',ondelete='CASCADE'),index=True)
    owner_id: Mapped[uuid.UUID|None]=mapped_column(ForeignKey('users.id',ondelete='SET NULL'),index=True)
    title: Mapped[str]=mapped_column(String(200),nullable=False,index=True)
    stage: Mapped[str]=mapped_column(String(50),nullable=False,default='lead',index=True)
    estimated_value: Mapped[float]=mapped_column(Float,nullable=False,default=0)
    probability: Mapped[int]=mapped_column(nullable=False,default=0)
    expected_close_date: Mapped[date|None]=mapped_column(Date)
    notes: Mapped[str|None]=mapped_column(Text)

class CRMTask(TimestampMixin, Base):
    __tablename__='crm_tasks'
    id: Mapped[uuid.UUID]=mapped_column(Uuid,primary_key=True,default=uuid.uuid4)
    organization_id: Mapped[uuid.UUID]=mapped_column(ForeignKey('organizations.id',ondelete='CASCADE'),index=True)
    client_id: Mapped[uuid.UUID|None]=mapped_column(ForeignKey('clients.id',ondelete='CASCADE'),index=True)
    opportunity_id: Mapped[uuid.UUID|None]=mapped_column(ForeignKey('crm_opportunities.id',ondelete='CASCADE'),index=True)
    assigned_to_id: Mapped[uuid.UUID|None]=mapped_column(ForeignKey('users.id',ondelete='SET NULL'),index=True)
    title: Mapped[str]=mapped_column(String(200),nullable=False)
    description: Mapped[str|None]=mapped_column(Text)
    status: Mapped[str]=mapped_column(String(40),nullable=False,default='pending',index=True)
    priority: Mapped[str]=mapped_column(String(20),nullable=False,default='normal',index=True)
    due_at: Mapped[datetime|None]=mapped_column(DateTime(timezone=True),index=True)
    completed_at: Mapped[datetime|None]=mapped_column(DateTime(timezone=True))


class LeadSource(TimestampMixin, Base):
    __tablename__ = "lead_sources"
    __table_args__ = (UniqueConstraint("organization_id", "code", name="uq_lead_sources_org_code"),)
    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    organization_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("organizations.id", ondelete="CASCADE"), index=True)
    code: Mapped[str] = mapped_column(String(50), nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)


class ServiceType(TimestampMixin, Base):
    __tablename__ = "service_types"
    __table_args__ = (UniqueConstraint("organization_id", "code", name="uq_service_types_org_code"),)
    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    organization_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("organizations.id", ondelete="CASCADE"), index=True)
    code: Mapped[str] = mapped_column(String(50), nullable=False)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)


class Lead(TimestampMixin, Base):
    __tablename__ = "leads"
    __table_args__ = (
        Index("ix_leads_org_status_updated", "organization_id", "status", "updated_at"),
        Index("ix_leads_org_owner_status", "organization_id", "owner_id", "status"),
    )
    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    organization_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("organizations.id", ondelete="CASCADE"), index=True)
    full_name: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    cpf: Mapped[str | None] = mapped_column(String(11), index=True)
    phone: Mapped[str | None] = mapped_column(String(30), index=True)
    whatsapp: Mapped[str | None] = mapped_column(String(30), index=True)
    email: Mapped[str | None] = mapped_column(String(320), index=True)
    city: Mapped[str | None] = mapped_column(String(120))
    state: Mapped[str | None] = mapped_column(String(2))
    birth_date: Mapped[date | None] = mapped_column(Date)
    source_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("lead_sources.id", ondelete="RESTRICT"), index=True)
    source_detail: Mapped[str | None] = mapped_column(String(200))
    service_type_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("service_types.id", ondelete="RESTRICT"), index=True)
    campaign: Mapped[str | None] = mapped_column(String(160))
    owner_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), index=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="NOVO", index=True)
    priority: Mapped[str] = mapped_column(String(20), nullable=False, default="NORMAL", index=True)
    initial_notes: Mapped[str | None] = mapped_column(Text)
    has_legal_demand: Mapped[bool | None] = mapped_column(Boolean)
    urgent: Mapped[bool | None] = mapped_column(Boolean)
    has_lawyer: Mapped[bool | None] = mapped_column(Boolean)
    has_ongoing_case: Mapped[bool | None] = mapped_column(Boolean)
    had_previous_proposal: Mapped[bool | None] = mapped_column(Boolean)
    can_afford: Mapped[bool | None] = mapped_column(Boolean)
    interest_level: Mapped[str | None] = mapped_column(String(10))
    approximate_debt: Mapped[float | None] = mapped_column(Numeric(14, 2))
    approximate_creditors: Mapped[int | None] = mapped_column(Integer)
    monthly_income: Mapped[float | None] = mapped_column(Numeric(14, 2))
    income_commitment_percent: Mapped[float | None] = mapped_column(Numeric(5, 2))
    delinquency_status: Mapped[str | None] = mapped_column(String(100))
    is_negative_listed: Mapped[bool | None] = mapped_column(Boolean)
    has_existing_lawsuit: Mapped[bool | None] = mapped_column(Boolean)
    lost_reason: Mapped[str | None] = mapped_column(String(60))
    lost_notes: Mapped[str | None] = mapped_column(Text)
    converted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    converted_by_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    client_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("clients.id", ondelete="SET NULL"), index=True)
    recovery_case_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("recovery_cases.id", ondelete="SET NULL"), index=True)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)


class LeadInteraction(TimestampMixin, Base):
    __tablename__ = "lead_interactions"
    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    organization_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("organizations.id", ondelete="CASCADE"), index=True)
    lead_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("leads.id", ondelete="CASCADE"), index=True)
    user_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    interaction_type: Mapped[str] = mapped_column(String(40), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class LeadTask(TimestampMixin, Base):
    __tablename__ = "lead_tasks"
    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    organization_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("organizations.id", ondelete="CASCADE"), index=True)
    lead_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("leads.id", ondelete="CASCADE"), index=True)
    assigned_to_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    description: Mapped[str] = mapped_column(String(300), nullable=False)
    due_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="PENDENTE")
    priority: Mapped[str] = mapped_column(String(20), nullable=False, default="NORMAL")
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class LeadProposal(TimestampMixin, Base):
    __tablename__ = "lead_proposals"
    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    organization_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("organizations.id", ondelete="CASCADE"), index=True)
    lead_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("leads.id", ondelete="CASCADE"), index=True)
    fixed_value: Mapped[float] = mapped_column(Numeric(14, 2), nullable=False, default=0)
    down_payment: Mapped[float] = mapped_column(Numeric(14, 2), nullable=False, default=0)
    installments: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    installment_value: Mapped[float] = mapped_column(Numeric(14, 2), nullable=False, default=0)
    success_percentage: Mapped[float] = mapped_column(Numeric(5, 2), nullable=False, default=0)
    valid_until: Mapped[date | None] = mapped_column(Date)
    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="RASCUNHO")
    notes: Mapped[str | None] = mapped_column(Text)
