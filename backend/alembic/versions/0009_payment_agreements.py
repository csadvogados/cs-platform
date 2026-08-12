"""Add payment agreements.

Revision ID: 0009_payment_agreements
Revises: 0008_add_client_payment_capacity
Create Date: 2026-08-12
"""

from alembic import op
import sqlalchemy as sa


revision = "0009_payment_agreements"
down_revision = "0008_add_client_payment_capacity"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "payment_agreements",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("organization_id", sa.Uuid(), nullable=False),
        sa.Column("client_id", sa.Uuid(), nullable=False),
        sa.Column("debt_id", sa.Uuid(), nullable=True),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("status", sa.String(length=30), nullable=False, server_default="active"),
        sa.Column("payment_method", sa.String(length=40), nullable=False),
        sa.Column("original_amount", sa.Numeric(14, 2), nullable=False, server_default="0"),
        sa.Column("negotiated_amount", sa.Numeric(14, 2), nullable=False),
        sa.Column("down_payment", sa.Numeric(14, 2), nullable=False, server_default="0"),
        sa.Column("installment_count", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("installment_amount", sa.Numeric(14, 2), nullable=False, server_default="0"),
        sa.Column("first_due_date", sa.Date(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["client_id"], ["clients.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["debt_id"], ["debts.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.CheckConstraint("negotiated_amount > 0", name="ck_payment_agreements_negotiated_positive"),
        sa.CheckConstraint("down_payment >= 0 AND down_payment <= negotiated_amount", name="ck_payment_agreements_down_payment"),
        sa.CheckConstraint("installment_count >= 1", name="ck_payment_agreements_installment_count"),
        sa.CheckConstraint("installment_amount >= 0", name="ck_payment_agreements_installment_amount"),
    )
    op.create_index("ix_payment_agreements_organization_id", "payment_agreements", ["organization_id"])
    op.create_index("ix_payment_agreements_client_id", "payment_agreements", ["client_id"])
    op.create_index("ix_payment_agreements_debt_id", "payment_agreements", ["debt_id"])
    op.create_index("ix_payment_agreements_status", "payment_agreements", ["status"])
    op.create_index("ix_payment_agreements_payment_method", "payment_agreements", ["payment_method"])


def downgrade() -> None:
    op.drop_index("ix_payment_agreements_payment_method", table_name="payment_agreements")
    op.drop_index("ix_payment_agreements_status", table_name="payment_agreements")
    op.drop_index("ix_payment_agreements_debt_id", table_name="payment_agreements")
    op.drop_index("ix_payment_agreements_client_id", table_name="payment_agreements")
    op.drop_index("ix_payment_agreements_organization_id", table_name="payment_agreements")
    op.drop_table("payment_agreements")
