"""Add collection queue assignment and priority.

Revision ID: 0013_collection_queue
Revises: 0012_action_cancellation
Create Date: 2026-08-25
"""

from alembic import op
import sqlalchemy as sa


revision = "0013_collection_queue"
down_revision = "0012_action_cancellation"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "payment_installments",
        sa.Column("collection_assigned_user_id", sa.Uuid(), nullable=True),
    )
    op.add_column(
        "payment_installments",
        sa.Column("collection_priority", sa.String(length=20), nullable=False, server_default="normal"),
    )
    op.create_foreign_key(
        "fk_payment_installments_collection_assigned_user_id_users",
        "payment_installments", "users", ["collection_assigned_user_id"], ["id"], ondelete="SET NULL",
    )
    op.create_index(
        "ix_payment_installments_collection_assigned_user_id",
        "payment_installments", ["collection_assigned_user_id"],
    )
    op.create_index(
        "ix_payment_installments_collection_priority",
        "payment_installments", ["collection_priority"],
    )
    op.alter_column("payment_installments", "collection_priority", server_default=None)


def downgrade() -> None:
    op.drop_index("ix_payment_installments_collection_priority", table_name="payment_installments")
    op.drop_index("ix_payment_installments_collection_assigned_user_id", table_name="payment_installments")
    op.drop_constraint(
        "fk_payment_installments_collection_assigned_user_id_users",
        "payment_installments", type_="foreignkey",
    )
    op.drop_column("payment_installments", "collection_priority")
    op.drop_column("payment_installments", "collection_assigned_user_id")
