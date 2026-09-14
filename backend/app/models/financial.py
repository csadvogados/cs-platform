import uuid
from decimal import Decimal
from sqlalchemy import Boolean, ForeignKey, Numeric, String, Text, Uuid
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
