"""Sprint 1 core models
Revision ID: 0001_sprint1
Revises:
"""
from alembic import op
import sqlalchemy as sa
revision="0001_sprint1"; down_revision=None; branch_labels=None; depends_on=None

def upgrade():
    op.create_table("organizations",sa.Column("id",sa.Uuid(),primary_key=True),sa.Column("legal_name",sa.String(200),nullable=False),sa.Column("trade_name",sa.String(200)),sa.Column("tax_id",sa.String(20),unique=True),sa.Column("status",sa.String(30),nullable=False),sa.Column("created_at",sa.DateTime(timezone=True),server_default=sa.func.now(),nullable=False),sa.Column("updated_at",sa.DateTime(timezone=True),server_default=sa.func.now(),nullable=False))
    op.create_table("users",sa.Column("id",sa.Uuid(),primary_key=True),sa.Column("organization_id",sa.Uuid(),sa.ForeignKey("organizations.id",ondelete="CASCADE"),nullable=False),sa.Column("full_name",sa.String(200),nullable=False),sa.Column("email",sa.String(320),nullable=False),sa.Column("password_hash",sa.String(500),nullable=False),sa.Column("role",sa.String(50),nullable=False),sa.Column("status",sa.String(30),nullable=False),sa.Column("is_superuser",sa.Boolean(),nullable=False),sa.Column("created_at",sa.DateTime(timezone=True),server_default=sa.func.now(),nullable=False),sa.Column("updated_at",sa.DateTime(timezone=True),server_default=sa.func.now(),nullable=False),sa.UniqueConstraint("organization_id","email"))
    op.create_index("ix_users_email","users",["email"]); op.create_index("ix_users_organization_id","users",["organization_id"])
    op.create_table("clients",sa.Column("id",sa.Uuid(),primary_key=True),sa.Column("organization_id",sa.Uuid(),sa.ForeignKey("organizations.id",ondelete="CASCADE"),nullable=False),sa.Column("assigned_user_id",sa.Uuid(),sa.ForeignKey("users.id",ondelete="SET NULL")),sa.Column("full_name",sa.String(200),nullable=False),sa.Column("cpf",sa.String(11),nullable=False),sa.Column("rg",sa.String(30)),sa.Column("birth_date",sa.Date()),sa.Column("profession",sa.String(120)),sa.Column("email",sa.String(320)),sa.Column("phone",sa.String(30)),sa.Column("city",sa.String(120)),sa.Column("state",sa.String(2)),sa.Column("status",sa.String(40),nullable=False),sa.Column("person_natural",sa.Boolean(),nullable=False),sa.Column("good_faith_declared",sa.Boolean()),sa.Column("notes",sa.Text()),sa.Column("created_at",sa.DateTime(timezone=True),server_default=sa.func.now(),nullable=False),sa.Column("updated_at",sa.DateTime(timezone=True),server_default=sa.func.now(),nullable=False),sa.UniqueConstraint("organization_id","cpf"))
    for name,cols in [("ix_clients_organization_id",["organization_id"]),("ix_clients_assigned_user_id",["assigned_user_id"]),("ix_clients_full_name",["full_name"]),("ix_clients_cpf",["cpf"]),("ix_clients_phone",["phone"]),("ix_clients_status",["status"])]: op.create_index(name,"clients",cols)
    op.create_table("audit_events",sa.Column("id",sa.Integer(),primary_key=True,autoincrement=True),sa.Column("organization_id",sa.Uuid()),sa.Column("user_id",sa.Uuid(),sa.ForeignKey("users.id",ondelete="SET NULL")),sa.Column("entity_type",sa.String(80),nullable=False),sa.Column("entity_id",sa.Uuid()),sa.Column("action",sa.String(40),nullable=False),sa.Column("new_values",sa.JSON()),sa.Column("occurred_at",sa.DateTime(timezone=True),server_default=sa.func.now(),nullable=False))

def downgrade():
    op.drop_table("audit_events"); op.drop_table("clients"); op.drop_table("users"); op.drop_table("organizations")
