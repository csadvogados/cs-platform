"""Create the missing financial domain tables.

Revision ID: 0007_financial_schema
Revises: 0006_crm_stabilization
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "0007_financial_schema"
down_revision = "0006_crm_stabilization"
branch_labels = None
depends_on = None


def timestamp_columns() -> list[sa.Column]:
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


def upgrade() -> None:
    op.create_table(
        "incomes",
        sa.Column("id", sa.Uuid(), primary_key=True, nullable=False),
        sa.Column(
            "client_id",
            sa.Uuid(),
            sa.ForeignKey("clients.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("income_type", sa.String(80), nullable=False),
        sa.Column("description", sa.String(200), nullable=True),
        sa.Column(
            "net_amount",
            sa.Numeric(14, 2),
            server_default="0",
            nullable=False,
        ),
        sa.Column(
            "recurring",
            sa.Boolean(),
            server_default=sa.true(),
            nullable=False,
        ),
        *timestamp_columns(),
    )
    op.create_index("ix_incomes_client_id", "incomes", ["client_id"])

    op.create_table(
        "expenses",
        sa.Column("id", sa.Uuid(), primary_key=True, nullable=False),
        sa.Column(
            "client_id",
            sa.Uuid(),
            sa.ForeignKey("clients.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("category", sa.String(80), nullable=False),
        sa.Column("description", sa.String(200), nullable=True),
        sa.Column(
            "amount",
            sa.Numeric(14, 2),
            server_default="0",
            nullable=False,
        ),
        sa.Column(
            "essential",
            sa.Boolean(),
            server_default=sa.true(),
            nullable=False,
        ),
        sa.Column(
            "recurring",
            sa.Boolean(),
            server_default=sa.true(),
            nullable=False,
        ),
        *timestamp_columns(),
    )
    op.create_index("ix_expenses_client_id", "expenses", ["client_id"])

    op.create_table(
        "creditors",
        sa.Column("id", sa.Uuid(), primary_key=True, nullable=False),
        sa.Column(
            "organization_id",
            sa.Uuid(),
            sa.ForeignKey("organizations.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("legal_name", sa.String(200), nullable=False),
        sa.Column("sac_phone", sa.String(30), nullable=True),
        sa.Column("sac_email", sa.String(200), nullable=True),
        sa.Column("ombudsman_phone", sa.String(30), nullable=True),
        sa.Column("ombudsman_email", sa.String(200), nullable=True),
        sa.Column(
            "consumer_gov_enabled",
            sa.Boolean(),
            server_default=sa.false(),
            nullable=False,
        ),
        *timestamp_columns(),
    )
    op.create_index(
        "ix_creditors_organization_id",
        "creditors",
        ["organization_id"],
    )
    op.create_index("ix_creditors_legal_name", "creditors", ["legal_name"])

    op.create_table(
        "debts",
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
            "creditor_id",
            sa.Uuid(),
            sa.ForeignKey("creditors.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("nature", sa.String(50), nullable=False),
        sa.Column(
            "current_balance",
            sa.Numeric(14, 2),
            server_default="0",
            nullable=False,
        ),
        sa.Column(
            "monthly_installment",
            sa.Numeric(14, 2),
            server_default="0",
            nullable=False,
        ),
        sa.Column(
            "overdue",
            sa.Boolean(),
            server_default=sa.false(),
            nullable=False,
        ),
        *timestamp_columns(),
    )
    op.create_index("ix_debts_organization_id", "debts", ["organization_id"])
    op.create_index("ix_debts_client_id", "debts", ["client_id"])
    op.create_index("ix_debts_nature", "debts", ["nature"])

    op.create_table(
        "diagnoses",
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
        sa.Column("version", sa.Integer(), server_default="1", nullable=False),
        sa.Column(
            "total_income",
            sa.Numeric(14, 2),
            server_default="0",
            nullable=False,
        ),
        sa.Column(
            "total_expenses",
            sa.Numeric(14, 2),
            server_default="0",
            nullable=False,
        ),
        sa.Column(
            "total_debt_balance",
            sa.Numeric(14, 2),
            server_default="0",
            nullable=False,
        ),
        sa.Column(
            "total_installments",
            sa.Numeric(14, 2),
            server_default="0",
            nullable=False,
        ),
        sa.Column(
            "disposable_income",
            sa.Numeric(14, 2),
            server_default="0",
            nullable=False,
        ),
        sa.Column(
            "commitment_percentage",
            sa.Numeric(7, 2),
            server_default="0",
            nullable=False,
        ),
        sa.Column(
            "minimum_existential_reference",
            sa.Numeric(14, 2),
            server_default="600",
            nullable=False,
        ),
        sa.Column(
            "eligibility_score",
            sa.Integer(),
            server_default="0",
            nullable=False,
        ),
        sa.Column("eligibility_result", sa.String(120), nullable=False),
        sa.Column("economic_conclusion", sa.Text(), nullable=False),
        sa.Column(
            "legal_alerts",
            sa.Text(),
            server_default="",
            nullable=False,
        ),
        *timestamp_columns(),
    )
    op.create_index(
        "ix_diagnoses_organization_id",
        "diagnoses",
        ["organization_id"],
    )
    op.create_index("ix_diagnoses_client_id", "diagnoses", ["client_id"])


def downgrade() -> None:
    op.drop_index("ix_diagnoses_client_id", table_name="diagnoses")
    op.drop_index("ix_diagnoses_organization_id", table_name="diagnoses")
    op.drop_table("diagnoses")

    op.drop_index("ix_debts_nature", table_name="debts")
    op.drop_index("ix_debts_client_id", table_name="debts")
    op.drop_index("ix_debts_organization_id", table_name="debts")
    op.drop_table("debts")

    op.drop_index("ix_creditors_legal_name", table_name="creditors")
    op.drop_index("ix_creditors_organization_id", table_name="creditors")
    op.drop_table("creditors")

    op.drop_index("ix_expenses_client_id", table_name="expenses")
    op.drop_table("expenses")

    op.drop_index("ix_incomes_client_id", table_name="incomes")
    op.drop_table("incomes")
