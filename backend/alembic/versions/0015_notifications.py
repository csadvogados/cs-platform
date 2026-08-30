"""Add persistent notifications and user preferences.

Revision ID: 0015_notifications
Revises: 0014_performance_goals
Create Date: 2026-08-26
"""
from alembic import op
import sqlalchemy as sa

revision = "0015_notifications"
down_revision = "0014_performance_goals"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "notifications",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("organization_id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("notification_type", sa.String(40), nullable=False),
        sa.Column("priority", sa.String(20), nullable=False, server_default="normal"),
        sa.Column("title", sa.String(200), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("target_view", sa.String(40), nullable=True),
        sa.Column("target_filter", sa.String(80), nullable=True),
        sa.Column("deduplication_key", sa.String(180), nullable=False),
        sa.Column("event_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("read_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "deduplication_key", name="uq_notifications_user_event"),
    )
    for column in ("organization_id", "user_id", "notification_type", "priority", "event_at", "read_at"):
        op.create_index(f"ix_notifications_{column}", "notifications", [column])
    op.create_table(
        "notification_preferences",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("organization_id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("tasks_enabled", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("collections_enabled", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("promises_enabled", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("goals_enabled", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("only_assigned_items", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id"),
    )
    op.create_index("ix_notification_preferences_organization_id", "notification_preferences", ["organization_id"])
    op.create_index("ix_notification_preferences_user_id", "notification_preferences", ["user_id"], unique=True)


def downgrade() -> None:
    op.drop_index("ix_notification_preferences_user_id", table_name="notification_preferences")
    op.drop_index("ix_notification_preferences_organization_id", table_name="notification_preferences")
    op.drop_table("notification_preferences")
    for column in reversed(("organization_id", "user_id", "notification_type", "priority", "event_at", "read_at")):
        op.drop_index(f"ix_notifications_{column}", table_name="notifications")
    op.drop_table("notifications")
