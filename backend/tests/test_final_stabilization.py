from pathlib import Path

import pytest

from app.api.routes.audit import sanitized_details
from app.core.config import Settings


ROOT = Path(__file__).parents[2]


def production_settings(**overrides):
    values = {
        "environment": "production",
        "database_url": "postgresql://user:password@database:5432/cs_platform",
        "secret_key": "a-production-secret-with-more-than-32-characters",
        "initial_admin_password": "AUniqueInitialPassword123!",
        "cors_origins": "https://cs-platform.example.com",
        "reset_admin_on_startup": False,
    }
    values.update(overrides)
    return Settings(**values)


def test_secure_production_configuration_is_accepted():
    production_settings().validate_runtime_security()


@pytest.mark.parametrize(
    ("override", "message"),
    [
        ({"secret_key": "CHANGE-ME-IN-PRODUCTION"}, "SECRET_KEY"),
        ({"initial_admin_password": "ChangeMe123!"}, "INITIAL_ADMIN_PASSWORD"),
        ({"database_url": "sqlite:///production.db"}, "PostgreSQL"),
        ({"cors_origins": "*"}, "CORS_ORIGINS"),
        ({"reset_admin_on_startup": True}, "RESET_ADMIN_ON_STARTUP"),
    ],
)
def test_insecure_production_configuration_fails_fast(override, message):
    with pytest.raises(RuntimeError, match=message):
        production_settings(**override).validate_runtime_security()


def test_audit_details_never_expose_credentials_or_full_documents():
    result = sanitized_details({
        "password": "NeverExposeMe",
        "refresh_token": "token-value",
        "secret_key": "secret-value",
        "cpf": "11144477735",
        "nested": {"password_hash": "hash-value", "cnpj": "11222333000181"},
    })
    assert result == {
        "password": "[PROTEGIDO]",
        "refresh_token": "[PROTEGIDO]",
        "secret_key": "[PROTEGIDO]",
        "cpf": "final 7735",
        "nested": {"password_hash": "[PROTEGIDO]", "cnpj": "final 0181"},
    }


def test_production_runbook_covers_backup_restore_and_incidents():
    checklist = (ROOT / "PRODUCTION_CHECKLIST.md").read_text(encoding="utf-8")
    assert "Backup e restauração no Railway" in checklist
    assert "banco temporário isolado" in checklist
    assert "Auditoria e resposta a incidentes" in checklist
    assert "METRICS_TOKEN" in checklist
