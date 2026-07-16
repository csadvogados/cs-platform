from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from typing import Any, Protocol

from fastapi import Depends

from app.core.enums import RoleType
from app.core.exceptions import AuthorizationException
from app.security.permissions import PermissionCode


class AuthenticatedUserProtocol(Protocol):
    role: str
    is_superuser: bool


ROLE_PERMISSIONS: dict[str, frozenset[str]] = {
    RoleType.ADMIN.value: frozenset(
        permission.value for permission in PermissionCode
    ),

    RoleType.SUPERVISOR.value: frozenset({
        PermissionCode.USER_READ.value,
        PermissionCode.CLIENT_CREATE.value,
        PermissionCode.CLIENT_READ.value,
        PermissionCode.CLIENT_UPDATE.value,
        PermissionCode.CLIENT_EXPORT.value,
        PermissionCode.CREDITOR_CREATE.value,
        PermissionCode.CREDITOR_READ.value,
        PermissionCode.CREDITOR_UPDATE.value,
        PermissionCode.DEBT_CREATE.value,
        PermissionCode.DEBT_READ.value,
        PermissionCode.DEBT_UPDATE.value,
        PermissionCode.NEGOTIATION_CREATE.value,
        PermissionCode.NEGOTIATION_READ.value,
        PermissionCode.NEGOTIATION_UPDATE.value,
        PermissionCode.NEGOTIATION_APPROVE.value,
        PermissionCode.DOCUMENT_UPLOAD.value,
        PermissionCode.DOCUMENT_READ.value,
        PermissionCode.DOCUMENT_VALIDATE.value,
        PermissionCode.DIAGNOSIS_CREATE.value,
        PermissionCode.DIAGNOSIS_READ.value,
        PermissionCode.DIAGNOSIS_UPDATE.value,
        PermissionCode.DIAGNOSIS_APPROVE.value,
        PermissionCode.DASHBOARD_READ.value,
        PermissionCode.REPORT_READ.value,
        PermissionCode.REPORT_EXPORT.value,
        PermissionCode.AUDIT_READ.value,
    }),

    RoleType.LAWYER.value: frozenset({
        PermissionCode.CLIENT_CREATE.value,
        PermissionCode.CLIENT_READ.value,
        PermissionCode.CLIENT_UPDATE.value,
        PermissionCode.CREDITOR_READ.value,
        PermissionCode.DEBT_CREATE.value,
        PermissionCode.DEBT_READ.value,
        PermissionCode.DEBT_UPDATE.value,
        PermissionCode.NEGOTIATION_CREATE.value,
        PermissionCode.NEGOTIATION_READ.value,
        PermissionCode.NEGOTIATION_UPDATE.value,
        PermissionCode.DOCUMENT_UPLOAD.value,
        PermissionCode.DOCUMENT_READ.value,
        PermissionCode.DOCUMENT_VALIDATE.value,
        PermissionCode.DIAGNOSIS_CREATE.value,
        PermissionCode.DIAGNOSIS_READ.value,
        PermissionCode.DIAGNOSIS_UPDATE.value,
        PermissionCode.DASHBOARD_READ.value,
        PermissionCode.REPORT_READ.value,
    }),

    RoleType.NEGOTIATOR.value: frozenset({
        PermissionCode.CLIENT_READ.value,
        PermissionCode.CLIENT_UPDATE.value,
        PermissionCode.CREDITOR_READ.value,
        PermissionCode.DEBT_READ.value,
        PermissionCode.DEBT_UPDATE.value,
        PermissionCode.NEGOTIATION_CREATE.value,
        PermissionCode.NEGOTIATION_READ.value,
        PermissionCode.NEGOTIATION_UPDATE.value,
        PermissionCode.DOCUMENT_READ.value,
        PermissionCode.DASHBOARD_READ.value,
    }),

    RoleType.FINANCIAL.value: frozenset({
        PermissionCode.CLIENT_READ.value,
        PermissionCode.CREDITOR_READ.value,
        PermissionCode.DEBT_READ.value,
        PermissionCode.DEBT_UPDATE.value,
        PermissionCode.NEGOTIATION_READ.value,
        PermissionCode.DOCUMENT_READ.value,
        PermissionCode.DASHBOARD_READ.value,
        PermissionCode.REPORT_READ.value,
        PermissionCode.REPORT_EXPORT.value,
    }),

    RoleType.SUPPORT.value: frozenset({
        PermissionCode.CLIENT_CREATE.value,
        PermissionCode.CLIENT_READ.value,
        PermissionCode.CLIENT_UPDATE.value,
        PermissionCode.CREDITOR_READ.value,
        PermissionCode.DOCUMENT_UPLOAD.value,
        PermissionCode.DOCUMENT_READ.value,
        PermissionCode.DASHBOARD_READ.value,
    }),

    RoleType.CLIENT.value: frozenset({
        PermissionCode.CLIENT_READ.value,
        PermissionCode.DEBT_READ.value,
        PermissionCode.NEGOTIATION_READ.value,
        PermissionCode.DOCUMENT_READ.value,
        PermissionCode.DIAGNOSIS_READ.value,
    }),
}


class RolePermissionRegistry:
    @staticmethod
    def permissions_for_role(role: str) -> frozenset[str]:
        return ROLE_PERMISSIONS.get(
            role.strip().lower(),
            frozenset(),
        )

    @staticmethod
    def has_permission(
        role: str,
        permission: str | PermissionCode,
    ) -> bool:
        permission_value = (
            permission.value
            if isinstance(permission, PermissionCode)
            else permission
        )

        return permission_value in (
            RolePermissionRegistry.permissions_for_role(role)
        )

    @staticmethod
    def has_all_permissions(
        role: str,
        permissions: Iterable[str | PermissionCode],
    ) -> bool:
        return all(
            RolePermissionRegistry.has_permission(role, permission)
            for permission in permissions
        )


@dataclass(frozen=True, slots=True)
class PermissionChecker:
    required_permissions: tuple[str, ...]

    def __call__(
        self,
        current_user: AuthenticatedUserProtocol,
    ) -> AuthenticatedUserProtocol:
        if getattr(current_user, "is_superuser", False):
            return current_user

        role = str(getattr(current_user, "role", "")).strip().lower()

        if not RolePermissionRegistry.has_all_permissions(
            role,
            self.required_permissions,
        ):
            raise AuthorizationException(
                details={
                    "required_permissions": list(
                        self.required_permissions
                    ),
                    "role": role,
                }
            )

        return current_user


def require_permissions(
    *permissions: str | PermissionCode,
) -> PermissionChecker:
    normalized_permissions = tuple(
        permission.value
        if isinstance(permission, PermissionCode)
        else permission
        for permission in permissions
    )

    return PermissionChecker(
        required_permissions=normalized_permissions,
    )


__all__ = [
    "ROLE_PERMISSIONS",
    "RolePermissionRegistry",
    "PermissionChecker",
    "require_permissions",
]
