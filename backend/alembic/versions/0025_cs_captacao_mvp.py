"""CS Captação / CRM MVP.

Revision ID: 0025_cs_captacao_mvp
Revises: 0024_judicial_closure
"""

from alembic import op
import sqlalchemy as sa

revision = "0025_cs_captacao_mvp"
down_revision = "0024_judicial_closure"
branch_labels = None
depends_on = None


def timestamps():
    return [
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    ]


def upgrade():
    op.create_table(
        "lead_sources",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "organization_id",
            sa.Uuid(),
            sa.ForeignKey("organizations.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("code", sa.String(50), nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("active", sa.Boolean(), server_default=sa.true(), nullable=False),
        *timestamps(),
        sa.UniqueConstraint(
            "organization_id",
            "code",
            name="uq_lead_sources_org_code",
        ),
    )
    op.create_index(
        "ix_lead_sources_organization_id",
        "lead_sources",
        ["organization_id"],
    )

    op.create_table(
        "service_types",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "organization_id",
            sa.Uuid(),
            sa.ForeignKey("organizations.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("code", sa.String(50), nullable=False),
        sa.Column("name", sa.String(120), nullable=False),
        sa.Column("active", sa.Boolean(), server_default=sa.true(), nullable=False),
        *timestamps(),
        sa.UniqueConstraint(
            "organization_id",
            "code",
            name="uq_service_types_org_code",
        ),
    )
    op.create_index(
        "ix_service_types_organization_id",
        "service_types",
        ["organization_id"],
    )

    op.create_table(
        "leads",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "organization_id",
            sa.Uuid(),
            sa.ForeignKey("organizations.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("full_name", sa.String(200), nullable=False),
        sa.Column("cpf", sa.String(11)),
        sa.Column("phone", sa.String(30)),
        sa.Column("whatsapp", sa.String(30)),
        sa.Column("email", sa.String(320)),
        sa.Column("city", sa.String(120)),
        sa.Column("state", sa.String(2)),
        sa.Column("birth_date", sa.Date()),
        sa.Column(
            "source_id",
            sa.Uuid(),
            sa.ForeignKey("lead_sources.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("source_detail", sa.String(200)),
        sa.Column(
            "service_type_id",
            sa.Uuid(),
            sa.ForeignKey("service_types.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("campaign", sa.String(160)),
        sa.Column(
            "owner_id",
            sa.Uuid(),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
        ),
        sa.Column("status", sa.String(20), server_default="NOVO", nullable=False),
        sa.Column("priority", sa.String(20), server_default="NORMAL", nullable=False),
        sa.Column("initial_notes", sa.Text()),
        sa.Column("has_legal_demand", sa.Boolean()),
        sa.Column("urgent", sa.Boolean()),
        sa.Column("has_lawyer", sa.Boolean()),
        sa.Column("has_ongoing_case", sa.Boolean()),
        sa.Column("had_previous_proposal", sa.Boolean()),
        sa.Column("can_afford", sa.Boolean()),
        sa.Column("interest_level", sa.String(10)),
        sa.Column("approximate_debt", sa.Numeric(14, 2)),
        sa.Column("approximate_creditors", sa.Integer()),
        sa.Column("monthly_income", sa.Numeric(14, 2)),
        sa.Column("income_commitment_percent", sa.Numeric(5, 2)),
        sa.Column("delinquency_status", sa.String(100)),
        sa.Column("is_negative_listed", sa.Boolean()),
        sa.Column("has_existing_lawsuit", sa.Boolean()),
        sa.Column("lost_reason", sa.String(60)),
        sa.Column("lost_notes", sa.Text()),
        sa.Column("converted_at", sa.DateTime(timezone=True)),
        sa.Column(
            "converted_by_id",
            sa.Uuid(),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
        ),
        sa.Column(
            "client_id",
            sa.Uuid(),
            sa.ForeignKey("clients.id", ondelete="SET NULL"),
        ),
        sa.Column(
            "recovery_case_id",
            sa.Uuid(),
            sa.ForeignKey("recovery_cases.id", ondelete="SET NULL"),
        ),
        sa.Column("deleted_at", sa.DateTime(timezone=True)),
        *timestamps(),
    )

    for name, cols in [
        ("ix_leads_organization_id", ["organization_id"]),
        ("ix_leads_full_name", ["full_name"]),
        ("ix_leads_cpf", ["cpf"]),
        ("ix_leads_phone", ["phone"]),
        ("ix_leads_whatsapp", ["whatsapp"]),
        ("ix_leads_email", ["email"]),
        ("ix_leads_source_id", ["source_id"]),
        ("ix_leads_service_type_id", ["service_type_id"]),
        ("ix_leads_client_id", ["client_id"]),
        ("ix_leads_recovery_case_id", ["recovery_case_id"]),
        ("ix_leads_deleted_at", ["deleted_at"]),
        ("ix_leads_org_status_updated", ["organization_id", "status", "updated_at"]),
        ("ix_leads_org_owner_status", ["organization_id", "owner_id", "status"]),
    ]:
        op.create_index(name, "leads", cols)

    op.create_table(
        "lead_interactions",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "organization_id",
            sa.Uuid(),
            sa.ForeignKey("organizations.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "lead_id",
            sa.Uuid(),
            sa.ForeignKey("leads.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "user_id",
            sa.Uuid(),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
        ),
        sa.Column("interaction_type", sa.String(40), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        *timestamps(),
    )
    op.create_index(
        "ix_lead_interactions_org_lead",
        "lead_interactions",
        ["organization_id", "lead_id"],
    )

    op.create_table(
        "lead_tasks",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "organization_id",
            sa.Uuid(),
            sa.ForeignKey("organizations.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "lead_id",
            sa.Uuid(),
            sa.ForeignKey("leads.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "assigned_to_id",
            sa.Uuid(),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
        ),
        sa.Column("description", sa.String(300), nullable=False),
        sa.Column("due_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("status", sa.String(20), server_default="PENDENTE", nullable=False),
        sa.Column("priority", sa.String(20), server_default="NORMAL", nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True)),
        *timestamps(),
    )
    op.create_index(
        "ix_lead_tasks_org_lead_due",
        "lead_tasks",
        ["organization_id", "lead_id", "due_at"],
    )

    op.create_table(
        "lead_proposals",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "organization_id",
            sa.Uuid(),
            sa.ForeignKey("organizations.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "lead_id",
            sa.Uuid(),
            sa.ForeignKey("leads.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("fixed_value", sa.Numeric(14, 2), server_default="0", nullable=False),
        sa.Column("down_payment", sa.Numeric(14, 2), server_default="0", nullable=False),
        sa.Column("installments", sa.Integer(), server_default="1", nullable=False),
        sa.Column(
            "installment_value",
            sa.Numeric(14, 2),
            server_default="0",
            nullable=False,
        ),
        sa.Column(
            "success_percentage",
            sa.Numeric(5, 2),
            server_default="0",
            nullable=False,
        ),
        sa.Column("valid_until", sa.Date()),
        sa.Column("sent_at", sa.DateTime(timezone=True)),
        sa.Column("status", sa.String(20), server_default="RASCUNHO", nullable=False),
        sa.Column("notes", sa.Text()),
        *timestamps(),
    )
    op.create_index(
        "ix_lead_proposals_org_lead",
        "lead_proposals",
        ["organization_id", "lead_id"],
    )


def downgrade():
    for table in [
        "lead_proposals",
        "lead_tasks",
        "lead_interactions",
        "leads",
        "service_types",
        "lead_sources",
    ]:
        op.drop_table(table)
