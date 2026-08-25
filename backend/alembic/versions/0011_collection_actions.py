"""Add collection actions and follow-up reminders.

Revision ID: 0011_collection_actions
Revises: 0010_payment_installments
Create Date: 2026-08-25
"""

from alembic import op
import sqlalchemy as sa


revision = "0011_collection_actions"
down_revision = "0010_payment_installments"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "collection_actions",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("organization_id", sa.Uuid(), nullable=False),
        sa.Column("client_id", sa.Uuid(), nullable=False),
        sa.Column("agreement_id", sa.Uuid(), nullable=False),
        sa.Column("installment_id", sa.Uuid(), nullable=False),
        sa.Column("created_by_user_id", sa.Uuid(), nullable=False),
        sa.Column("action_type", sa.String(length=30), nullable=False),
        sa.Column("outcome", sa.String(length=30), nullable=False),
        sa.Column("contacted_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("notes", sa.Text(), nullable=False),
        sa.Column("promise_date", sa.Date(), nullable=True),
        sa.Column("promise_amount", sa.Numeric(14, 2), nullable=True),
        sa.Column("next_follow_up_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["agreement_id"], ["payment_agreements.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["client_id"], ["clients.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["created_by_user_id"], ["users.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["installment_id"], ["payment_installments.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.CheckConstraint("promise_amount IS NULL OR promise_amount > 0", name="ck_collection_actions_promise_amount"),
    )
    for column in (
        "organization_id", "client_id", "agreement_id", "installment_id", "created_by_user_id",
        "action_type", "outcome", "contacted_at", "promise_date", "next_follow_up_at",
    ):
        op.create_index(f"ix_collection_actions_{column}", "collection_actions", [column])


def downgrade() -> None:
    op.drop_table("collection_actions")
