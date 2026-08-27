"""Create the Recovery Core case aggregate.

Revision ID: 0016_recovery_cases
Revises: 0015_notifications
"""
from alembic import op
import sqlalchemy as sa

revision = "0016_recovery_cases"
down_revision = "0015_notifications"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "recovery_cases",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("organization_id", sa.Uuid(), nullable=False),
        sa.Column("client_id", sa.Uuid(), nullable=False),
        sa.Column("case_number", sa.String(32), nullable=False),
        sa.Column("status", sa.String(24), nullable=False, server_default="draft"),
        sa.Column("stage", sa.String(32), nullable=False, server_default="intake"),
        sa.Column("source", sa.String(24), nullable=False, server_default="manual"),
        sa.Column("assigned_user_id", sa.Uuid(), nullable=True),
        sa.Column("opened_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("closed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("closure_reason", sa.Text(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["client_id"], ["clients.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["assigned_user_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("organization_id", "case_number", name="uq_recovery_cases_org_number"),
    )
    for column in ("organization_id", "client_id", "status", "stage", "assigned_user_id", "deleted_at"):
        op.create_index(f"ix_recovery_cases_{column}", "recovery_cases", [column])
    op.create_index("ix_recovery_cases_org_status_updated", "recovery_cases", ["organization_id", "status", "updated_at"])
    op.create_index("ix_recovery_cases_org_assignee_stage", "recovery_cases", ["organization_id", "assigned_user_id", "stage"])


def downgrade() -> None:
    op.drop_index("ix_recovery_cases_org_assignee_stage", table_name="recovery_cases")
    op.drop_index("ix_recovery_cases_org_status_updated", table_name="recovery_cases")
    for column in reversed(("organization_id", "client_id", "status", "stage", "assigned_user_id", "deleted_at")):
        op.drop_index(f"ix_recovery_cases_{column}", table_name="recovery_cases")
    op.drop_table("recovery_cases")
