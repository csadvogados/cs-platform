"""Add the missing client payment-capacity field.

Revision ID: 0008_add_client_payment_capacity
Revises: 0007_financial_schema
Create Date: 2026-08-04
"""

from alembic import op
import sqlalchemy as sa


revision = "0008_add_client_payment_capacity"
down_revision = "0007_financial_schema"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "clients",
        sa.Column("can_pay_without_harming_basics", sa.Boolean(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("clients", "can_pay_without_harming_basics")
