from app.core.constants import ALLOWED_SORT_ORDERS, APP_VERSION, DEFAULT_PAGE_SIZE, MAX_PAGE_SIZE, SYSTEM_ROLES


def test_core_constants():
    assert APP_VERSION == "5.4.1"
    assert DEFAULT_PAGE_SIZE < MAX_PAGE_SIZE
    assert ALLOWED_SORT_ORDERS == ("asc", "desc")
    assert "admin" in SYSTEM_ROLES
