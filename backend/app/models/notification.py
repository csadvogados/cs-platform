import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text, UniqueConstraint, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin


class Notification(TimestampMixin, Base):
    __tablename__ = "notifications"
    __table_args__ = (UniqueConstraint("user_id", "deduplication_key", name="uq_notifications_user_event"),)

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    organization_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("organizations.id", ondelete="CASCADE"), index=True)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    notification_type: Mapped[str] = mapped_column(String(40), nullable=False, index=True)
    priority: Mapped[str] = mapped_column(String(20), nullable=False, default="normal", index=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    target_view: Mapped[str | None] = mapped_column(String(40))
    target_filter: Mapped[str | None] = mapped_column(String(80))
    deduplication_key: Mapped[str] = mapped_column(String(180), nullable=False)
    event_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    read_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)

    user = relationship("User")


class NotificationPreference(TimestampMixin, Base):
    __tablename__ = "notification_preferences"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    organization_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("organizations.id", ondelete="CASCADE"), index=True)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), unique=True, index=True)
    tasks_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    collections_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    promises_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    goals_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    only_assigned_items: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    user = relationship("User")
