from app.security.password_policy import PasswordPolicy


def test_strong_password_is_valid():
    result = PasswordPolicy.validate(
        "SenhaForte2026!",
        email="admin@example.com",
    )

    assert result.is_valid is True
    assert result.errors == []


def test_weak_password_is_invalid():
    result = PasswordPolicy.validate("123")

    assert result.is_valid is False
    assert len(result.errors) >= 3
