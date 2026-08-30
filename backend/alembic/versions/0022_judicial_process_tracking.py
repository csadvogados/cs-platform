"""Add judicial process tracking.

Revision ID: 0022_judicial_process_tracking
Revises: 0021_client_documents
"""
from alembic import op
import sqlalchemy as sa

revision = "0022_judicial_process_tracking"
down_revision = "0021_client_documents"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "judicial_processes",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("organization_id", sa.Uuid(), nullable=False),
        sa.Column("recovery_case_id", sa.Uuid(), nullable=False),
        sa.Column("process_number", sa.String(length=40), nullable=False),
        sa.Column("court", sa.String(length=160), nullable=False),
        sa.Column("district", sa.String(length=160), nullable=True),
        sa.Column("division", sa.String(length=160), nullable=True),
        sa.Column("filed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="filed"),
        sa.Column("next_deadline", sa.DateTime(timezone=True), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["recovery_case_id"], ["recovery_cases.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("recovery_case_id", name="uq_judicial_processes_recovery_case"),
        sa.UniqueConstraint("organization_id", "process_number", name="uq_judicial_processes_org_number"),
    )
    op.create_index("ix_judicial_processes_organization_id", "judicial_processes", ["organization_id"])
    op.create_index("ix_judicial_processes_recovery_case_id", "judicial_processes", ["recovery_case_id"])
    op.create_index("ix_judicial_processes_status", "judicial_processes", ["status"])
    op.create_index("ix_judicial_processes_next_deadline", "judicial_processes", ["next_deadline"])
    op.create_index("ix_judicial_processes_org_status_updated", "judicial_processes", ["organization_id", "status", "updated_at"])
    op.create_table(
        "judicial_process_events",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("organization_id", sa.Uuid(), nullable=False),
        sa.Column("judicial_process_id", sa.Uuid(), nullable=False),
        sa.Column("created_by_user_id", sa.Uuid(), nullable=True),
        sa.Column("event_date", sa.DateTime(timezone=True), nullable=False),
        sa.Column("event_type", sa.String(length=32), nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["judicial_process_id"], ["judicial_processes.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["created_by_user_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_judicial_process_events_organization_id", "judicial_process_events", ["organization_id"])
    op.create_index("ix_judicial_process_events_judicial_process_id", "judicial_process_events", ["judicial_process_id"])
    op.create_index("ix_judicial_process_events_org_process_date", "judicial_process_events", ["organization_id", "judicial_process_id", "event_date"])


def downgrade() -> None:
    op.drop_table("judicial_process_events")
    op.drop_table("judicial_processes")
