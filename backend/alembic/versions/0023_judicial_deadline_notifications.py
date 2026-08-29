"""Add judicial deadline notification preference.

Revision ID: 0023_judicial_deadlines
Revises: 0022_judicial_process_tracking
"""
from alembic import op
import sqlalchemy as sa

revision = "0023_judicial_deadlines"
down_revision = "0022_judicial_process_tracking"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("notification_preferences", sa.Column("judicial_enabled", sa.Boolean(), nullable=False, server_default=sa.true()))
    op.alter_column("notification_preferences", "judicial_enabled", server_default=None)


def downgrade() -> None:
    op.drop_column("notification_preferences", "judicial_enabled")
