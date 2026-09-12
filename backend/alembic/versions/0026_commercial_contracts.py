"""Commercial proposals and contracts.

Revision ID: 0026_commercial_contracts
Revises: 0025_cs_captacao_mvp
"""
from alembic import op
import sqlalchemy as sa

revision = "0026_commercial_contracts"
down_revision = "0025_cs_captacao_mvp"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "commercial_contracts",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("organization_id", sa.Uuid(), sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("lead_id", sa.Uuid(), sa.ForeignKey("leads.id", ondelete="CASCADE"), nullable=False),
        sa.Column("proposal_id", sa.Uuid(), sa.ForeignKey("lead_proposals.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("client_id", sa.Uuid(), sa.ForeignKey("clients.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("contract_number", sa.String(40), nullable=False),
        sa.Column("title", sa.String(200), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("status", sa.String(20), server_default="RASCUNHO", nullable=False),
        sa.Column("version", sa.Integer(), server_default="1", nullable=False),
        sa.Column("approved_by_id", sa.Uuid(), sa.ForeignKey("users.id", ondelete="SET NULL")),
        sa.Column("approved_at", sa.DateTime(timezone=True)),
        sa.Column("sent_at", sa.DateTime(timezone=True)),
        sa.Column("signed_at", sa.DateTime(timezone=True)),
        sa.Column("signature_reference", sa.String(300)),
        sa.Column("notes", sa.Text()),
        sa.Column("deleted_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("proposal_id"),
        sa.UniqueConstraint("organization_id", "contract_number", name="uq_contract_org_number"),
    )
    for name, columns in (
        ("ix_contract_org_lead", ["organization_id", "lead_id"]),
        ("ix_contract_org_client", ["organization_id", "client_id"]),
        ("ix_contract_org_status", ["organization_id", "status"]),
    ):
        op.create_index(name, "commercial_contracts", columns)


def downgrade():
    op.drop_table("commercial_contracts")
