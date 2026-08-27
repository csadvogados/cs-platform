"""Expand diagnosis snapshots and decision support.

Revision ID: 0017_diagnosis_engine_v2
Revises: 0016_recovery_cases
"""
from alembic import op
import sqlalchemy as sa

revision = "0017_diagnosis_engine_v2"
down_revision = "0016_recovery_cases"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("diagnoses", sa.Column("risk_level", sa.String(24), nullable=False, server_default="moderate"))
    op.add_column("diagnoses", sa.Column("recommended_strategy", sa.String(80), nullable=False, server_default="manual_review"))
    op.add_column("diagnoses", sa.Column("max_payment_capacity", sa.Numeric(14, 2), nullable=False, server_default="0"))
    op.add_column("diagnoses", sa.Column("data_quality_score", sa.Integer(), nullable=False, server_default="0"))
    op.add_column("diagnoses", sa.Column("score_breakdown", sa.JSON(), nullable=False, server_default=sa.text("'{}'")))
    op.add_column("diagnoses", sa.Column("analysis_snapshot", sa.JSON(), nullable=False, server_default=sa.text("'{}'")))
    op.create_index("ix_diagnoses_risk_level", "diagnoses", ["risk_level"])
    op.create_index("ix_diagnoses_org_risk_created", "diagnoses", ["organization_id", "risk_level", "created_at"])


def downgrade() -> None:
    op.drop_index("ix_diagnoses_org_risk_created", table_name="diagnoses")
    op.drop_index("ix_diagnoses_risk_level", table_name="diagnoses")
    for column in ("analysis_snapshot", "score_breakdown", "data_quality_score", "max_payment_capacity", "recommended_strategy", "risk_level"):
        op.drop_column("diagnoses", column)
