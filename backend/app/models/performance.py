import uuid
from datetime import date
from decimal import Decimal

from sqlalchemy import Date, ForeignKey, Index, Numeric, String, UniqueConstraint, Uuid, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin


class PerformanceGoal(TimestampMixin, Base):
    __tablename__ = "performance_goals"
    __table_args__ = (
        UniqueConstraint(
            "organization_id", "reference_month", "metric", "user_id",
            name="uq_performance_goals_scope",
        ),
        Index(
            "uq_performance_goals_organization_metric",
            "organization_id", "reference_month", "metric",
            unique=True,
            postgresql_where=text("user_id IS NULL"),
            sqlite_where=text("user_id IS NULL"),
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    organization_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    user_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=True, index=True
    )
    reference_month: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    metric: Mapped[str] = mapped_column(String(40), nullable=False, index=True)
    target_value: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)

    user = relationship("User")
