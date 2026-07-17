"""Organization Engine

Revision ID: 0002_organization_engine
Revises: 0001_sprint1
"""

from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "0002_organization_engine"
down_revision: Union[str, None] = "0001_sprint1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    op.add_column("organizations", sa.Column("state_registration", sa.String(30), nullable=True))
    op.add_column("organizations", sa.Column("municipal_registration", sa.String(30), nullable=True))
    op.add_column(
        "organizations",
        sa.Column("organization_type", sa.String(30), nullable=False, server_default="law_firm"),
    )
    op.add_column("organizations", sa.Column("email", sa.String(320), nullable=True))
    op.add_column("organizations", sa.Column("phone", sa.String(30), nullable=True))
    op.add_column("organizations", sa.Column("website", sa.String(255), nullable=True))
    op.add_column("organizations", sa.Column("description", sa.Text(), nullable=True))
    op.add_column(
        "organizations",
        sa.Column("is_system_default", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.create_index("ix_organizations_organization_type", "organizations", ["organization_type"])
    op.create_index("ix_organizations_status", "organizations", ["status"])

    op.create_table(
        "organization_settings",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("organization_id", sa.Uuid(), nullable=False),
        sa.Column("timezone", sa.String(80), nullable=False, server_default="America/Sao_Paulo"),
        sa.Column("language", sa.String(20), nullable=False, server_default="pt-BR"),
        sa.Column("currency", sa.String(3), nullable=False, server_default="BRL"),
        sa.Column("date_format", sa.String(30), nullable=False, server_default="DD/MM/YYYY"),
        sa.Column("allow_client_portal", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("allow_external_integrations", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("require_mfa_for_admins", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("organization_id"),
    )
    op.create_index("ix_organization_settings_organization_id", "organization_settings", ["organization_id"])

    op.create_table(
        "organization_branding",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("organization_id", sa.Uuid(), nullable=False),
        sa.Column("public_name", sa.String(200), nullable=True),
        sa.Column("logo_url", sa.String(500), nullable=True),
        sa.Column("favicon_url", sa.String(500), nullable=True),
        sa.Column("primary_color", sa.String(20), nullable=False, server_default="#0F172A"),
        sa.Column("secondary_color", sa.String(20), nullable=False, server_default="#2563EB"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("organization_id"),
    )
    op.create_index("ix_organization_branding_organization_id", "organization_branding", ["organization_id"])

    op.create_table(
        "organization_licenses",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("organization_id", sa.Uuid(), nullable=False),
        sa.Column("plan", sa.String(30), nullable=False, server_default="starter"),
        sa.Column("status", sa.String(30), nullable=False, server_default="trial"),
        sa.Column("starts_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("max_users", sa.Integer(), nullable=False, server_default="5"),
        sa.Column("max_storage_mb", sa.Integer(), nullable=False, server_default="1024"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("organization_id"),
    )
    op.create_index("ix_organization_licenses_organization_id", "organization_licenses", ["organization_id"])
    op.create_index("ix_organization_licenses_plan", "organization_licenses", ["plan"])
    op.create_index("ix_organization_licenses_status", "organization_licenses", ["status"])

    op.create_table(
        "organization_addresses",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("organization_id", sa.Uuid(), nullable=False),
        sa.Column("address_type", sa.String(30), nullable=False, server_default="headquarters"),
        sa.Column("postal_code", sa.String(12), nullable=True),
        sa.Column("street", sa.String(255), nullable=True),
        sa.Column("number", sa.String(30), nullable=True),
        sa.Column("complement", sa.String(120), nullable=True),
        sa.Column("district", sa.String(120), nullable=True),
        sa.Column("city", sa.String(120), nullable=True),
        sa.Column("state", sa.String(2), nullable=True),
        sa.Column("country", sa.String(2), nullable=False, server_default="BR"),
        sa.Column("is_primary", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_organization_addresses_organization_id", "organization_addresses", ["organization_id"])
    op.create_index("ix_organization_addresses_address_type", "organization_addresses", ["address_type"])

    op.execute(
        """
        UPDATE organizations
        SET is_system_default = TRUE
        WHERE id = (
            SELECT id FROM organizations ORDER BY created_at ASC LIMIT 1
        )
        """
    )

def downgrade() -> None:
    op.drop_table("organization_addresses")
    op.drop_table("organization_licenses")
    op.drop_table("organization_branding")
    op.drop_table("organization_settings")
    op.drop_index("ix_organizations_status", table_name="organizations")
    op.drop_index("ix_organizations_organization_type", table_name="organizations")
    op.drop_column("organizations", "is_system_default")
    op.drop_column("organizations", "description")
    op.drop_column("organizations", "website")
    op.drop_column("organizations", "phone")
    op.drop_column("organizations", "email")
    op.drop_column("organizations", "organization_type")
    op.drop_column("organizations", "municipal_registration")
    op.drop_column("organizations", "state_registration")
