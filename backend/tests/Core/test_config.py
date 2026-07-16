from app.core.config import Settings


def test_settings_builds_cors_list():
    settings = Settings(
        secret_key="test-secret",
        cors_origins="http://localhost:3000,https://example.com",
    )
    assert settings.cors_origin_list == [
        "http://localhost:3000",
        "https://example.com",
    ]


def test_settings_detects_production():
    settings = Settings(
        secret_key="test-secret",
        environment="production",
    )
    assert settings.is_production is True
