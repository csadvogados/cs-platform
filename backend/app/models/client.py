import uuid
from datetime import date
from sqlalchemy import Boolean, Date, ForeignKey, String, Text, UniqueConstraint, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base, TimestampMixin
from app.models.enums import ClientStatus

class Client(TimestampMixin, Base):
    __tablename__ = "clients"
    __table_args__ = (UniqueConstraint("organization_id", "cpf"),)
    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    organization_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("organizations.id", ondelete="CASCADE"), index=True)
    assigned_user_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), index=True)
    full_name: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    cpf: Mapped[str] = mapped_column(String(11), nullable=False, index=True)
    rg: Mapped[str | None] = mapped_column(String(30))
    birth_date: Mapped[date | None] = mapped_column(Date)
    profession: Mapped[str | None] = mapped_column(String(120))
    email: Mapped[str | None] = mapped_column(String(320))
    phone: Mapped[str | None] = mapped_column(String(30), index=True)
    city: Mapped[str | None] = mapped_column(String(120))
    state: Mapped[str | None] = mapped_column(String(2))
    status: Mapped[str] = mapped_column(String(40), default=ClientStatus.LEAD.value, nullable=False, index=True)
    person_natural: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    good_faith_declared: Mapped[bool | None] = mapped_column(Boolean)
    can_pay_without_harming_basics: Mapped[bool | None] = mapped_column(Boolean)
    notes: Mapped[str | None] = mapped_column(Text)
    organization = relationship("Organization", back_populates="clients")
    assigned_user = relationship("User")
    incomes = relationship("Income", back_populates="client", cascade="all, delete-orphan")
    expenses = relationship("Expense", back_populates="client", cascade="all, delete-orphan")
    debts = relationship("Debt", back_populates="client", cascade="all, delete-orphan")
    diagnoses = relationship("Diagnosis", back_populates="client", cascade="all, delete-orphan")
