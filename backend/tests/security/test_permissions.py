from app.security.permissions import PermissionCode
from app.security.rbac import RolePermissionRegistry


def test_admin_has_all_permissions():
    assert RolePermissionRegistry.has_permission(
        "admin",
        PermissionCode.USER_CREATE,
    ) is True


def test_support_cannot_manage_roles():
    assert RolePermissionRegistry.has_permission(
        "atendimento",
        PermissionCode.USER_MANAGE_ROLES,
    ) is False
