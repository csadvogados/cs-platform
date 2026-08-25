"""Add auditable collection action cancellation.

Revision ID: 0012_collection_action_cancellation
Revises: 0011_collection_actions
Create Date: 2026-08-25
"""

from alembic import op
import sqlalchemy as sa


revision = "0012_collection_action_cancellation"
down_revision = "0011_collection_actions"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("collection_actions", sa.Column("cancelled_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("collection_actions", sa.Column("cancelled_by_user_id", sa.Uuid(), nullable=True))
    op.add_column("collection_actions", sa.Column("cancellation_reason", sa.Text(), nullable=True))
    op.create_foreign_key(
        "fk_collection_actions_cancelled_by_user_id_users",
        "collection_actions", "users", ["cancelled_by_user_id"], ["id"], ondelete="SET NULL",
    )
    op.create_index("ix_collection_actions_cancelled_at", "collection_actions", ["cancelled_at"])
    op.create_index("ix_collection_actions_cancelled_by_user_id", "collection_actions", ["cancelled_by_user_id"])


def downgrade() -> None:
    op.drop_index("ix_collection_actions_cancelled_by_user_id", table_name="collection_actions")
    op.drop_index("ix_collection_actions_cancelled_at", table_name="collection_actions")
    op.drop_constraint("fk_collection_actions_cancelled_by_user_id_users", "collection_actions", type_="foreignkey")
    op.drop_column("collection_actions", "cancellation_reason")
    op.drop_column("collection_actions", "cancelled_by_user_id")
    op.drop_column("collection_actions", "cancelled_at")
