import uuid
from datetime import date, datetime
from decimal import Decimal
from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Integer, Numeric, String, Text, UniqueConstraint, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base, TimestampMixin

class Income(TimestampMixin, Base):
    __tablename__ = "incomes"
    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    client_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("clients.id", ondelete="CASCADE"), index=True)
    income_type: Mapped[str] = mapped_column(String(80), nullable=False)
    description: Mapped[str | None] = mapped_column(String(200))
    net_amount: Mapped[Decimal] = mapped_column(Numeric(14,2), default=0, nullable=False)
    recurring: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    client = relationship("Client", back_populates="incomes")

class Expense(TimestampMixin, Base):
    __tablename__ = "expenses"
    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    client_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("clients.id", ondelete="CASCADE"), index=True)
    category: Mapped[str] = mapped_column(String(80), nullable=False)
    description: Mapped[str | None] = mapped_column(String(200))
    amount: Mapped[Decimal] = mapped_column(Numeric(14,2), default=0, nullable=False)
    essential: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    recurring: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    client = relationship("Client", back_populates="expenses")

class Creditor(TimestampMixin, Base):
    __tablename__ = "creditors"
    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    organization_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("organizations.id", ondelete="CASCADE"), index=True)
    legal_name: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    sac_phone: Mapped[str | None] = mapped_column(String(30))
    sac_email: Mapped[str | None] = mapped_column(String(200))
    ombudsman_phone: Mapped[str | None] = mapped_column(String(30))
    ombudsman_email: Mapped[str | None] = mapped_column(String(200))
    consumer_gov_enabled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

class Debt(TimestampMixin, Base):
    __tablename__ = "debts"
    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    organization_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("organizations.id", ondelete="CASCADE"), index=True)
    client_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("clients.id", ondelete="CASCADE"), index=True)
    creditor_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("creditors.id", ondelete="SET NULL"))
    nature: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    current_balance: Mapped[Decimal] = mapped_column(Numeric(14,2), default=0, nullable=False)
    monthly_installment: Mapped[Decimal] = mapped_column(Numeric(14,2), default=0, nullable=False)
    overdue: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    client = relationship("Client", back_populates="debts")
    creditor = relationship("Creditor")


class PaymentAgreement(TimestampMixin, Base):
    __tablename__ = "payment_agreements"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    organization_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"), index=True
    )
    client_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("clients.id", ondelete="CASCADE"), index=True
    )
    debt_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("debts.id", ondelete="SET NULL"), index=True
    )
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="active", index=True)
    payment_method: Mapped[str] = mapped_column(String(40), nullable=False, index=True)
    original_amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=0, nullable=False)
    negotiated_amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=0, nullable=False)
    down_payment: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=0, nullable=False)
    installment_count: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    installment_amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=0, nullable=False)
    first_due_date: Mapped[date | None] = mapped_column(Date)
    notes: Mapped[str | None] = mapped_column(Text)

    client = relationship("Client")
    debt = relationship("Debt")
    installments = relationship(
        "PaymentInstallment",
        back_populates="agreement",
        cascade="all, delete-orphan",
        order_by="PaymentInstallment.installment_number",
    )


class PaymentInstallment(TimestampMixin, Base):
    __tablename__ = "payment_installments"
    __table_args__ = (
        UniqueConstraint("agreement_id", "installment_number", name="uq_payment_installments_agreement_number"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    organization_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"), index=True
    )
    client_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("clients.id", ondelete="CASCADE"), index=True
    )
    agreement_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("payment_agreements.id", ondelete="CASCADE"), index=True
    )
    installment_number: Mapped[int] = mapped_column(Integer, nullable=False)
    due_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="pending", index=True)
    paid_amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False, default=0)
    paid_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    payment_method: Mapped[str | None] = mapped_column(String(40), nullable=True)
    payment_notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    agreement = relationship("PaymentAgreement", back_populates="installments")
    collection_actions = relationship(
        "CollectionAction",
        back_populates="installment",
        cascade="all, delete-orphan",
        order_by="CollectionAction.contacted_at.desc()",
    )


class CollectionAction(TimestampMixin, Base):
    __tablename__ = "collection_actions"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    organization_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"), index=True
    )
    client_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("clients.id", ondelete="CASCADE"), index=True
    )
    agreement_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("payment_agreements.id", ondelete="CASCADE"), index=True
    )
    installment_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("payment_installments.id", ondelete="CASCADE"), index=True
    )
    created_by_user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"), index=True
    )
    action_type: Mapped[str] = mapped_column(String(30), nullable=False, index=True)
    outcome: Mapped[str] = mapped_column(String(30), nullable=False, index=True)
    contacted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    notes: Mapped[str] = mapped_column(Text, nullable=False)
    promise_date: Mapped[date | None] = mapped_column(Date, nullable=True, index=True)
    promise_amount: Mapped[Decimal | None] = mapped_column(Numeric(14, 2), nullable=True)
    next_follow_up_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, index=True)

    installment = relationship("PaymentInstallment", back_populates="collection_actions")
    created_by = relationship("User")

class Diagnosis(TimestampMixin, Base):
    __tablename__ = "diagnoses"
    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    organization_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("organizations.id", ondelete="CASCADE"), index=True)
    client_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("clients.id", ondelete="CASCADE"), index=True)
    version: Mapped[int] = mapped_column(default=1, nullable=False)
    total_income: Mapped[Decimal] = mapped_column(Numeric(14,2), default=0, nullable=False)
    total_expenses: Mapped[Decimal] = mapped_column(Numeric(14,2), default=0, nullable=False)
    total_debt_balance: Mapped[Decimal] = mapped_column(Numeric(14,2), default=0, nullable=False)
    total_installments: Mapped[Decimal] = mapped_column(Numeric(14,2), default=0, nullable=False)
    disposable_income: Mapped[Decimal] = mapped_column(Numeric(14,2), default=0, nullable=False)
    commitment_percentage: Mapped[Decimal] = mapped_column(Numeric(7,2), default=0, nullable=False)
    minimum_existential_reference: Mapped[Decimal] = mapped_column(Numeric(14,2), default=600, nullable=False)
    eligibility_score: Mapped[int] = mapped_column(default=0, nullable=False)
    eligibility_result: Mapped[str] = mapped_column(String(120), nullable=False)
    economic_conclusion: Mapped[str] = mapped_column(Text, nullable=False)
    legal_alerts: Mapped[str] = mapped_column(Text, default="", nullable=False)
    client = relationship("Client", back_populates="diagnoses")
