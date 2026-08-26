"""Add monthly organization and team performance goals.

Revision ID: 0014_performance_goals
Revises: 0013_collection_queue
Create Date: 2026-08-26
"""

from alembic import op
import sqlalchemy as sa


revision = "0014_performance_goals"
down_revision = "0013_collection_queue"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "performance_goals",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("organization_id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=True),
        sa.Column("reference_month", sa.Date(), nullable=False),
        sa.Column("metric", sa.String(length=40), nullable=False),
        sa.Column("target_value", sa.Numeric(14, 2), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "organization_id", "reference_month", "metric", "user_id",
            name="uq_performance_goals_scope",
        ),
    )
    op.create_index("ix_performance_goals_organization_id", "performance_goals", ["organization_id"])
    op.create_index("ix_performance_goals_user_id", "performance_goals", ["user_id"])
    op.create_index("ix_performance_goals_reference_month", "performance_goals", ["reference_month"])
    op.create_index("ix_performance_goals_metric", "performance_goals", ["metric"])
    op.create_index(
        "uq_performance_goals_organization_metric",
        "performance_goals",
        ["organization_id", "reference_month", "metric"],
        unique=True,
        postgresql_where=sa.text("user_id IS NULL"),
    )


def downgrade() -> None:
    op.drop_index("uq_performance_goals_organization_metric", table_name="performance_goals")
    op.drop_index("ix_performance_goals_metric", table_name="performance_goals")
    op.drop_index("ix_performance_goals_reference_month", table_name="performance_goals")
    op.drop_index("ix_performance_goals_user_id", table_name="performance_goals")
    op.drop_index("ix_performance_goals_organization_id", table_name="performance_goals")
    op.drop_table("performance_goals")
