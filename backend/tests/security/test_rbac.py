from dataclasses import dataclass

import pytest

from app.core.exceptions import AuthorizationException
from app.security.permissions import PermissionCode
from app.security.rbac import require_permissions


@dataclass
class FakeUser:
    role: str
    is_superuser: bool = False


def test_superuser_bypasses_permission_check():
    checker = require_permissions(
        PermissionCode.USER_MANAGE_ROLES
    )

    user = FakeUser(
        role="atendimento",
        is_superuser=True,
    )

    assert checker(user) is user


def test_missing_permission_raises():
    checker = require_permissions(
        PermissionCode.USER_MANAGE_ROLES
    )

    with pytest.raises(AuthorizationException):
        checker(
            FakeUser(
                role="atendimento",
                is_superuser=False,
            )
        )
