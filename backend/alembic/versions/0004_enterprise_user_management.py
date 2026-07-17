"""Enterprise User Management v5.3.0

Revision ID: 0004_enterprise_user_management
Revises: 0003_merge_auth_organization
"""
from alembic import op
import sqlalchemy as sa

revision = "0004_enterprise_user_management"
down_revision = "0003_merge_auth_organization"
branch_labels = None
depends_on = None

def upgrade():
    op.add_column("users", sa.Column("password_changed_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("users", sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True))
    op.create_index("ix_users_deleted_at", "users", ["deleted_at"])
    op.create_table("permissions",
        sa.Column("id", sa.Uuid(), primary_key=True), sa.Column("code", sa.String(120), nullable=False),
        sa.Column("name", sa.String(160), nullable=False), sa.Column("module", sa.String(80), nullable=False),
        sa.Column("description", sa.Text()), sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False), sa.UniqueConstraint("code"))
    op.create_index("ix_permissions_code", "permissions", ["code"]); op.create_index("ix_permissions_module", "permissions", ["module"])
    op.create_table("roles",
        sa.Column("id", sa.Uuid(), primary_key=True), sa.Column("organization_id", sa.Uuid(), sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(100), nullable=False), sa.Column("slug", sa.String(80), nullable=False), sa.Column("description", sa.Text()),
        sa.Column("is_system", sa.Boolean(), server_default=sa.false(), nullable=False), sa.Column("is_active", sa.Boolean(), server_default=sa.true(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False), sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("organization_id", "slug"))
    op.create_index("ix_roles_organization_id", "roles", ["organization_id"])
    op.create_table("role_permissions", sa.Column("role_id", sa.Uuid(), sa.ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True), sa.Column("permission_id", sa.Uuid(), sa.ForeignKey("permissions.id", ondelete="CASCADE"), primary_key=True))
    op.create_table("user_roles", sa.Column("user_id", sa.Uuid(), sa.ForeignKey("users.id", ondelete="CASCADE"), primary_key=True), sa.Column("role_id", sa.Uuid(), sa.ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True))
    op.create_table("user_invitations",
        sa.Column("id", sa.Uuid(), primary_key=True), sa.Column("organization_id", sa.Uuid(), sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("email", sa.String(320), nullable=False), sa.Column("full_name", sa.String(200), nullable=False), sa.Column("role_id", sa.Uuid(), sa.ForeignKey("roles.id", ondelete="SET NULL")),
        sa.Column("token_hash", sa.String(64), nullable=False), sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False), sa.Column("accepted_at", sa.DateTime(timezone=True)), sa.Column("revoked_at", sa.DateTime(timezone=True)),
        sa.Column("created_by_id", sa.Uuid(), sa.ForeignKey("users.id", ondelete="SET NULL")), sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False), sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False), sa.UniqueConstraint("token_hash"))
    op.create_index("ix_user_invitations_organization_id", "user_invitations", ["organization_id"]); op.create_index("ix_user_invitations_email", "user_invitations", ["email"])
    op.create_table("user_sessions",
        sa.Column("id", sa.Uuid(), primary_key=True), sa.Column("organization_id", sa.Uuid(), sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False), sa.Column("user_id", sa.Uuid(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("refresh_token_hash", sa.String(64), nullable=False, unique=True), sa.Column("ip_address", sa.String(64)), sa.Column("user_agent", sa.String(500)), sa.Column("last_activity_at", sa.DateTime(timezone=True), nullable=False), sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False), sa.Column("revoked_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False), sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False))
    op.create_index("ix_user_sessions_organization_id", "user_sessions", ["organization_id"]); op.create_index("ix_user_sessions_user_id", "user_sessions", ["user_id"])
    op.create_table("password_history", sa.Column("id", sa.Uuid(), primary_key=True), sa.Column("user_id", sa.Uuid(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False), sa.Column("password_hash", sa.String(500), nullable=False), sa.Column("created_at", sa.DateTime(timezone=True), nullable=False))
    op.create_index("ix_password_history_user_id", "password_history", ["user_id"])

def downgrade():
    op.drop_table("password_history"); op.drop_table("user_sessions"); op.drop_table("user_invitations"); op.drop_table("user_roles"); op.drop_table("role_permissions"); op.drop_table("roles"); op.drop_table("permissions")
    op.drop_index("ix_users_deleted_at", table_name="users"); op.drop_column("users", "deleted_at"); op.drop_column("users", "password_changed_at")
