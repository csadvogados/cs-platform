"""Merge Auth Enterprise and Organization Engine branches.

Revision ID: 0003_merge_auth_organization
Revises: 0002_auth_enterprise, 0002_organization_engine
"""

from collections.abc import Sequence

revision: str = "0003_merge_auth_organization"
down_revision: tuple[str, str] = (
    "0002_auth_enterprise",
    "0002_organization_engine",
)
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Merge-only revision: no database objects are changed."""


def downgrade() -> None:
    """Return to the two branch heads."""
