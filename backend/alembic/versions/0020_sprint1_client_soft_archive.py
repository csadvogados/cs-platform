"""Add Sprint 1 soft archive support to clients.

Revision ID: 0020_sprint1_client_soft_archive
Revises: 0019_offer_agreement_conversion
"""
from alembic import op
import sqlalchemy as sa

revision = "0020_sprint1_client_soft_archive"
down_revision = "0019_offer_agreement_conversion"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("clients", sa.Column("archived_at", sa.DateTime(timezone=True), nullable=True))
    op.create_index("ix_clients_archived_at", "clients", ["archived_at"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_clients_archived_at", table_name="clients")
    op.drop_column("clients", "archived_at")

