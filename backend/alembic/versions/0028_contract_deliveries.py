"""Contract delivery tracking.

Revision ID: 0028_contract_deliveries
Revises: 0027_contract_templates
"""
from alembic import op
import sqlalchemy as sa

revision = "0028_contract_deliveries"
down_revision = "0027_contract_templates"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("commercial_contracts", sa.Column("signature_due_at", sa.Date(), nullable=True))
    op.add_column("commercial_contracts", sa.Column("delivery_channel", sa.String(20), nullable=True))
    op.add_column("commercial_contracts", sa.Column("delivery_recipient", sa.String(320), nullable=True))
    op.create_index("ix_contract_signature_due", "commercial_contracts", ["organization_id", "signature_due_at"])
    op.create_table(
        "contract_deliveries",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("organization_id", sa.Uuid(), sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("contract_id", sa.Uuid(), sa.ForeignKey("commercial_contracts.id", ondelete="CASCADE"), nullable=False),
        sa.Column("sent_by_id", sa.Uuid(), sa.ForeignKey("users.id", ondelete="SET NULL")),
        sa.Column("channel", sa.String(20), nullable=False),
        sa.Column("recipient", sa.String(320), nullable=False),
        sa.Column("signature_due_at", sa.Date(), nullable=False),
        sa.Column("notes", sa.Text()),
        sa.Column("sent_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_contract_delivery_org", "contract_deliveries", ["organization_id"])
    op.create_index("ix_contract_delivery_contract", "contract_deliveries", ["contract_id"])


def downgrade():
    op.drop_table("contract_deliveries")
    op.drop_index("ix_contract_signature_due", table_name="commercial_contracts")
    op.drop_column("commercial_contracts", "delivery_recipient")
    op.drop_column("commercial_contracts", "delivery_channel")
    op.drop_column("commercial_contracts", "signature_due_at")
