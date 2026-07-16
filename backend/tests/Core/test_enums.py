from app.core.enums import RoleType, UserStatus


def test_enum_values():
    assert RoleType.ADMIN.value == "admin"
    assert UserStatus.ACTIVE.value == "active"


def test_base_str_enum_helpers():
    assert RoleType.has_value("admin") is True
    assert RoleType.has_value("inexistente") is False
    assert "advogado" in RoleType.values()
