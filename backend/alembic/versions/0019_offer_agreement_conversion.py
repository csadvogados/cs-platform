"""Link accepted negotiation offers to agreements.

Revision ID: 0019_offer_agreement_conversion
Revises: 0018_negotiation_engine
"""
from alembic import op
import sqlalchemy as sa

revision = "0019_offer_agreement_conversion"
down_revision = "0018_negotiation_engine"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("negotiation_offers", sa.Column("agreement_id", sa.Uuid(), nullable=True))
    op.add_column("negotiation_offers", sa.Column("converted_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("negotiation_offers", sa.Column("converted_by_user_id", sa.Uuid(), nullable=True))
    op.create_foreign_key("fk_negotiation_offers_agreement_id", "negotiation_offers", "payment_agreements", ["agreement_id"], ["id"], ondelete="SET NULL")
    op.create_foreign_key("fk_negotiation_offers_converted_by_user_id", "negotiation_offers", "users", ["converted_by_user_id"], ["id"], ondelete="SET NULL")
    op.create_index("ix_negotiation_offers_agreement_id", "negotiation_offers", ["agreement_id"], unique=True)


def downgrade() -> None:
    op.drop_index("ix_negotiation_offers_agreement_id", table_name="negotiation_offers")
    op.drop_constraint("fk_negotiation_offers_converted_by_user_id", "negotiation_offers", type_="foreignkey")
    op.drop_constraint("fk_negotiation_offers_agreement_id", "negotiation_offers", type_="foreignkey")
    op.drop_column("negotiation_offers", "converted_by_user_id")
    op.drop_column("negotiation_offers", "converted_at")
    op.drop_column("negotiation_offers", "agreement_id")
