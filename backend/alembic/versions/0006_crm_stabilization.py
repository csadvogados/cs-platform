"""CRM stabilization and query indexes v5.4.1."""
from alembic import op

revision = "0006_crm_stabilization"
down_revision = "0005_crm_enterprise"
branch_labels = None
depends_on = None


def upgrade():
    op.create_index("ix_crm_contacts_org_name", "crm_contacts", ["organization_id", "name"])
    op.create_index("ix_crm_interactions_org_occurred", "crm_interactions", ["organization_id", "occurred_at"])
    op.create_index("ix_crm_opportunities_org_stage_updated", "crm_opportunities", ["organization_id", "stage", "updated_at"])
    op.create_index("ix_crm_tasks_org_status_due", "crm_tasks", ["organization_id", "status", "due_at"])
    op.create_index("ix_crm_tasks_org_assignee_status", "crm_tasks", ["organization_id", "assigned_to_id", "status"])


def downgrade():
    op.drop_index("ix_crm_tasks_org_assignee_status", table_name="crm_tasks")
    op.drop_index("ix_crm_tasks_org_status_due", table_name="crm_tasks")
    op.drop_index("ix_crm_opportunities_org_stage_updated", table_name="crm_opportunities")
    op.drop_index("ix_crm_interactions_org_occurred", table_name="crm_interactions")
    op.drop_index("ix_crm_contacts_org_name", table_name="crm_contacts")
