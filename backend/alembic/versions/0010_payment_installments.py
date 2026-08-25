"""Add payment installments.

Revision ID: 0010_payment_installments
Revises: 0009_payment_agreements
Create Date: 2026-08-25
"""

from alembic import op
import sqlalchemy as sa


revision = "0010_payment_installments"
down_revision = "0009_payment_agreements"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "payment_installments",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("organization_id", sa.Uuid(), nullable=False),
        sa.Column("client_id", sa.Uuid(), nullable=False),
        sa.Column("agreement_id", sa.Uuid(), nullable=False),
        sa.Column("installment_number", sa.Integer(), nullable=False),
        sa.Column("due_date", sa.Date(), nullable=False),
        sa.Column("amount", sa.Numeric(14, 2), nullable=False),
        sa.Column("status", sa.String(length=30), nullable=False, server_default="pending"),
        sa.Column("paid_amount", sa.Numeric(14, 2), nullable=False, server_default="0"),
        sa.Column("paid_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("payment_method", sa.String(length=40), nullable=True),
        sa.Column("payment_notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["agreement_id"], ["payment_agreements.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["client_id"], ["clients.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("agreement_id", "installment_number", name="uq_payment_installments_agreement_number"),
        sa.CheckConstraint("installment_number >= 1", name="ck_payment_installments_number"),
        sa.CheckConstraint("amount > 0", name="ck_payment_installments_amount"),
        sa.CheckConstraint("paid_amount >= 0", name="ck_payment_installments_paid_amount"),
    )
    op.create_index("ix_payment_installments_organization_id", "payment_installments", ["organization_id"])
    op.create_index("ix_payment_installments_client_id", "payment_installments", ["client_id"])
    op.create_index("ix_payment_installments_agreement_id", "payment_installments", ["agreement_id"])
    op.create_index("ix_payment_installments_due_date", "payment_installments", ["due_date"])
    op.create_index("ix_payment_installments_status", "payment_installments", ["status"])


def downgrade() -> None:
    op.drop_index("ix_payment_installments_status", table_name="payment_installments")
    op.drop_index("ix_payment_installments_due_date", table_name="payment_installments")
    op.drop_index("ix_payment_installments_agreement_id", table_name="payment_installments")
    op.drop_index("ix_payment_installments_client_id", table_name="payment_installments")
    op.drop_index("ix_payment_installments_organization_id", table_name="payment_installments")
    op.drop_table("payment_installments")
