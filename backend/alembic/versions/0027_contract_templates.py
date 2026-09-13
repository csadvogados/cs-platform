"""Configurable commercial contract templates.

Revision ID: 0027_contract_templates
Revises: 0026_commercial_contracts
"""
from alembic import op
import sqlalchemy as sa

revision = "0027_contract_templates"
down_revision = "0026_commercial_contracts"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "contract_templates",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("organization_id", sa.Uuid(), sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("service_type_id", sa.Uuid(), sa.ForeignKey("service_types.id", ondelete="SET NULL")),
        sa.Column("name", sa.String(150), nullable=False),
        sa.Column("title", sa.String(200), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("active", sa.Boolean(), server_default=sa.true(), nullable=False),
        sa.Column("created_by_id", sa.Uuid(), sa.ForeignKey("users.id", ondelete="SET NULL")),
        sa.Column("deleted_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("organization_id", "name", name="uq_contract_template_org_name"),
    )
    op.create_index("ix_contract_template_org", "contract_templates", ["organization_id"])
    op.create_index("ix_contract_template_service", "contract_templates", ["service_type_id"])
    op.create_index("ix_contract_template_deleted", "contract_templates", ["deleted_at"])
    op.add_column("commercial_contracts", sa.Column("template_id", sa.Uuid(), nullable=True))
    op.create_foreign_key("fk_contract_template", "commercial_contracts", "contract_templates", ["template_id"], ["id"], ondelete="SET NULL")
    op.create_index("ix_commercial_contract_template", "commercial_contracts", ["template_id"])


def downgrade():
    op.drop_index("ix_commercial_contract_template", table_name="commercial_contracts")
    op.drop_constraint("fk_contract_template", "commercial_contracts", type_="foreignkey")
    op.drop_column("commercial_contracts", "template_id")
    op.drop_table("contract_templates")
