"""Add controlled judicial process closure.

Revision ID: 0024_judicial_closure
Revises: 0023_judicial_deadlines
"""
from alembic import op
import sqlalchemy as sa

revision = "0024_judicial_closure"
down_revision = "0023_judicial_deadlines"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("judicial_processes", sa.Column("outcome", sa.String(length=32), nullable=True))
    op.add_column("judicial_processes", sa.Column("closed_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("judicial_processes", sa.Column("closure_reason", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("judicial_processes", "closure_reason")
    op.drop_column("judicial_processes", "closed_at")
    op.drop_column("judicial_processes", "outcome")
