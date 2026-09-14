"""CS Captação / CRM MVP v5.5.0.

Revision ID: 0007_cs_captacao_mvp
Revises: 0006_crm_stabilization
"""

from alembic import op
import sqlalchemy as sa


revision = "0007_cs_captacao_mvp"
down_revision = "0006_crm_stabilization"
branch_labels = None
depends_on = None


def upgrade():
    # Auditoria: passa a guardar estado anterior e posterior.
    op.add_column(
        "audit_events",
        sa.Column("old_values", sa.JSON(), nullable=True),
    )

    # Oportunidade passa a representar o lead comercial do CS Captação.
    op.add_column(
        "crm_opportunities",
        sa.Column("source", sa.String(length=80), nullable=True),
    )
    op.add_column(
        "crm_opportunities",
        sa.Column("service", sa.String(length=120), nullable=True),
    )
    op.add_column(
        "crm_opportunities",
        sa.Column("next_contact_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "crm_opportunities",
        sa.Column(
            "stage_changed_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )
    op.add_column(
        "crm_opportunities",
        sa.Column("converted_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "crm_opportunities",
        sa.Column("lost_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "crm_opportunities",
        sa.Column("lost_reason", sa.Text(), nullable=True),
    )

    op.create_index(
        "ix_crm_opportunities_org_source",
        "crm_opportunities",
        ["organization_id", "source"],
    )
    op.create_index(
        "ix_crm_opportunities_org_service",
        "crm_opportunities",
        ["organization_id", "service"],
    )
    op.create_index(
        "ix_crm_opportunities_org_next_contact",
        "crm_opportunities",
        ["organization_id", "next_contact_at"],
    )

    # Compatibilidade com a nomenclatura do pipeline anterior.
    op.execute(
        "UPDATE crm_opportunities SET stage = 'new' WHERE stage = 'lead'"
    )
    op.execute(
        "UPDATE crm_opportunities SET stage = 'proposal' WHERE stage = 'negotiation'"
    )
    op.execute(
        "UPDATE crm_opportunities SET stage = 'converted' WHERE stage = 'won'"
    )
    op.execute(
        "UPDATE crm_opportunities SET stage_changed_at = updated_at"
    )
    op.execute(
        "UPDATE crm_opportunities SET converted_at = updated_at WHERE stage = 'converted' AND converted_at IS NULL"
    )
    op.execute(
        "UPDATE crm_opportunities SET lost_at = updated_at WHERE stage = 'lost' AND lost_at IS NULL"
    )

    # Interações podem ser vinculadas diretamente à oportunidade/lead.
    op.add_column(
        "crm_interactions",
        sa.Column("opportunity_id", sa.Uuid(), nullable=True),
    )
    op.create_foreign_key(
        "fk_crm_interactions_opportunity_id_crm_opportunities",
        "crm_interactions",
        "crm_opportunities",
        ["opportunity_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_index(
        "ix_crm_interactions_opportunity_id",
        "crm_interactions",
        ["opportunity_id"],
    )

    # Histórico imutável das mudanças de etapa do funil.
    op.create_table(
        "crm_opportunity_stage_history",
        sa.Column("id", sa.Uuid(), primary_key=True, nullable=False),
        sa.Column(
            "organization_id",
            sa.Uuid(),
            sa.ForeignKey("organizations.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "opportunity_id",
            sa.Uuid(),
            sa.ForeignKey("crm_opportunities.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "changed_by_id",
            sa.Uuid(),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("from_stage", sa.String(length=50), nullable=True),
        sa.Column("to_stage", sa.String(length=50), nullable=False),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column(
            "changed_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )
    op.create_index(
        "ix_crm_stage_history_org_opportunity",
        "crm_opportunity_stage_history",
        ["organization_id", "opportunity_id", "changed_at"],
    )
    op.create_index(
        "ix_crm_stage_history_changed_by",
        "crm_opportunity_stage_history",
        ["changed_by_id"],
    )

    # Núcleo mínimo de caso para permitir Lead -> Cliente -> Caso CS Recupera.
    op.create_table(
        "cases",
        sa.Column("id", sa.Uuid(), primary_key=True, nullable=False),
        sa.Column(
            "organization_id",
            sa.Uuid(),
            sa.ForeignKey("organizations.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "client_id",
            sa.Uuid(),
            sa.ForeignKey("clients.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "opportunity_id",
            sa.Uuid(),
            sa.ForeignKey("crm_opportunities.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "assigned_user_id",
            sa.Uuid(),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "service",
            sa.String(length=120),
            nullable=False,
            server_default="CS Recupera",
        ),
        sa.Column("title", sa.String(length=250), nullable=False),
        sa.Column(
            "status",
            sa.String(length=40),
            nullable=False,
            server_default="triage",
        ),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.UniqueConstraint(
            "organization_id",
            "opportunity_id",
            name="uq_cases_organization_opportunity",
        ),
    )
    op.create_index("ix_cases_organization_id", "cases", ["organization_id"])
    op.create_index("ix_cases_client_id", "cases", ["client_id"])
    op.create_index("ix_cases_opportunity_id", "cases", ["opportunity_id"])
    op.create_index("ix_cases_assigned_user_id", "cases", ["assigned_user_id"])
    op.create_index("ix_cases_status", "cases", ["status"])


def downgrade():
    op.drop_index("ix_cases_status", table_name="cases")
    op.drop_index("ix_cases_assigned_user_id", table_name="cases")
    op.drop_index("ix_cases_opportunity_id", table_name="cases")
    op.drop_index("ix_cases_client_id", table_name="cases")
    op.drop_index("ix_cases_organization_id", table_name="cases")
    op.drop_table("cases")

    op.drop_index(
        "ix_crm_stage_history_changed_by",
        table_name="crm_opportunity_stage_history",
    )
    op.drop_index(
        "ix_crm_stage_history_org_opportunity",
        table_name="crm_opportunity_stage_history",
    )
    op.drop_table("crm_opportunity_stage_history")

    op.drop_index(
        "ix_crm_interactions_opportunity_id",
        table_name="crm_interactions",
    )
    op.drop_constraint(
        "fk_crm_interactions_opportunity_id_crm_opportunities",
        "crm_interactions",
        type_="foreignkey",
    )
    op.drop_column("crm_interactions", "opportunity_id")

    op.execute(
        "UPDATE crm_opportunities SET stage = 'lead' WHERE stage = 'new'"
    )
    op.execute(
        "UPDATE crm_opportunities SET stage = 'won' WHERE stage = 'converted'"
    )
    op.execute(
        "UPDATE crm_opportunities SET stage = 'lead' WHERE stage = 'contacted'"
    )

    op.drop_index(
        "ix_crm_opportunities_org_next_contact",
        table_name="crm_opportunities",
    )
    op.drop_index(
        "ix_crm_opportunities_org_service",
        table_name="crm_opportunities",
    )
    op.drop_index(
        "ix_crm_opportunities_org_source",
        table_name="crm_opportunities",
    )
    op.drop_column("crm_opportunities", "lost_reason")
    op.drop_column("crm_opportunities", "lost_at")
    op.drop_column("crm_opportunities", "converted_at")
    op.drop_column("crm_opportunities", "stage_changed_at")
    op.drop_column("crm_opportunities", "next_contact_at")
    op.drop_column("crm_opportunities", "service")
    op.drop_column("crm_opportunities", "source")

    op.drop_column("audit_events", "old_values")
