from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from app.models.organization import Organization
from app.models.user import User
from app.security.permissions import PermissionCode
from app.security.rbac import RolePermissionRegistry


@dataclass(frozen=True, slots=True)
class IdentityContext:
    user: User
    organization: Organization
    permissions: frozenset[str]

    @property
    def user_id(self) -> UUID:
        return self.user.id

    @property
    def organization_id(self) -> UUID:
        return self.organization.id

    @property
    def role(self) -> str:
        return self.user.role

    @property
    def is_superuser(self) -> bool:
        return self.user.is_superuser

    def can_access_organization(self, organization_id: UUID) -> bool:
        return self.is_superuser or self.organization_id == organization_id

    @classmethod
    def from_entities(
        cls,
        *,
        user: User,
        organization: Organization,
    ) -> "IdentityContext":
        permissions = (
            frozenset(permission.value for permission in PermissionCode)
            if user.is_superuser
            else RolePermissionRegistry.permissions_for_role(user.role)
        )
        return cls(
            user=user,
            organization=organization,
            permissions=permissions,
        )


__all__ = ["IdentityContext"]
