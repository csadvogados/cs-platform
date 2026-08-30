"""Create Negotiation Engine tables.

Revision ID: 0018_negotiation_engine
Revises: 0017_diagnosis_engine_v2
"""
from alembic import op
import sqlalchemy as sa

revision = "0018_negotiation_engine"
down_revision = "0017_diagnosis_engine_v2"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table("negotiations",
        sa.Column("id", sa.Uuid(), nullable=False), sa.Column("organization_id", sa.Uuid(), nullable=False),
        sa.Column("recovery_case_id", sa.Uuid(), nullable=False), sa.Column("client_id", sa.Uuid(), nullable=False),
        sa.Column("debt_id", sa.Uuid(), nullable=False), sa.Column("creditor_id", sa.Uuid(), nullable=True),
        sa.Column("assigned_user_id", sa.Uuid(), nullable=True), sa.Column("status", sa.String(24), nullable=False, server_default="open"),
        sa.Column("channel", sa.String(24), nullable=False, server_default="other"), sa.Column("external_reference", sa.String(120)),
        sa.Column("opened_at", sa.DateTime(timezone=True), nullable=False), sa.Column("expires_at", sa.DateTime(timezone=True)),
        sa.Column("closed_at", sa.DateTime(timezone=True)), sa.Column("closure_reason", sa.Text()), sa.Column("notes", sa.Text()),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["recovery_case_id"], ["recovery_cases.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["client_id"], ["clients.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["debt_id"], ["debts.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["creditor_id"], ["creditors.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["assigned_user_id"], ["users.id"], ondelete="SET NULL"), sa.PrimaryKeyConstraint("id"))
    for column in ("organization_id", "recovery_case_id", "client_id", "debt_id", "creditor_id", "assigned_user_id", "status", "expires_at"):
        op.create_index(f"ix_negotiations_{column}", "negotiations", [column])
    op.create_index("ix_negotiations_org_status_updated", "negotiations", ["organization_id", "status", "updated_at"])
    op.create_table("negotiation_offers",
        sa.Column("id", sa.Uuid(), nullable=False), sa.Column("organization_id", sa.Uuid(), nullable=False),
        sa.Column("negotiation_id", sa.Uuid(), nullable=False), sa.Column("created_by_user_id", sa.Uuid(), nullable=False),
        sa.Column("sequence_number", sa.Integer(), nullable=False), sa.Column("origin", sa.String(20), nullable=False),
        sa.Column("original_amount", sa.Numeric(14,2), nullable=False), sa.Column("offered_amount", sa.Numeric(14,2), nullable=False),
        sa.Column("down_payment", sa.Numeric(14,2), nullable=False, server_default="0"), sa.Column("installment_count", sa.Integer(), nullable=False),
        sa.Column("installment_amount", sa.Numeric(14,2), nullable=False), sa.Column("annual_interest_rate", sa.Numeric(7,4), nullable=False, server_default="0"),
        sa.Column("first_due_date", sa.Date(), nullable=False), sa.Column("valid_until", sa.DateTime(timezone=True)),
        sa.Column("sustainable", sa.Boolean(), nullable=False, server_default=sa.false()), sa.Column("capacity_usage_percentage", sa.Numeric(7,2), nullable=False, server_default="0"),
        sa.Column("engine_score", sa.Integer(), nullable=False, server_default="0"), sa.Column("engine_decision", sa.String(24), nullable=False),
        sa.Column("engine_reason", sa.Text(), nullable=False), sa.Column("status", sa.String(24), nullable=False, server_default="pending"),
        sa.Column("responded_at", sa.DateTime(timezone=True)), sa.Column("notes", sa.Text()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["negotiation_id"], ["negotiations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["created_by_user_id"], ["users.id"], ondelete="RESTRICT"), sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("negotiation_id", "sequence_number", name="uq_negotiation_offers_sequence"))
    for column in ("organization_id", "negotiation_id", "created_by_user_id", "sustainable", "engine_decision", "status"):
        op.create_index(f"ix_negotiation_offers_{column}", "negotiation_offers", [column])
    op.create_index("ix_negotiation_offers_org_decision_created", "negotiation_offers", ["organization_id", "engine_decision", "created_at"])


def downgrade() -> None:
    op.drop_table("negotiation_offers")
    op.drop_table("negotiations")
