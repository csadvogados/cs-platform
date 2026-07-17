from pathlib import Path

from app.core.constants import APP_VERSION


BACKEND = Path(__file__).resolve().parents[1]


def test_release_version_is_v542():
    assert APP_VERSION == "5.4.2"


def test_docker_entrypoint_uses_runtime_port_and_runs_migrations():
    content = (BACKEND / "docker-entrypoint.sh").read_text(encoding="utf-8")
    assert 'PORT="${PORT:-8000}"' in content
    assert "alembic upgrade head" in content
    assert 'exec python -m uvicorn' in content
    assert '--port "$PORT"' in content


def test_railway_has_no_start_command_or_duplicate_predeploy_migration():
    content = (BACKEND / "railway.json").read_text(encoding="utf-8")
    assert '"startCommand"' not in content
    assert '"preDeployCommand"' not in content
    assert '"healthcheckPath": "/api/v1/health"' in content


def test_required_migration_is_packaged():
    migration = BACKEND / "alembic" / "versions" / "0006_crm_stabilization.py"
    assert migration.exists()
    content = migration.read_text(encoding="utf-8")
    assert 'revision = "0006_crm_stabilization"' in content
    assert 'down_revision = "0005_crm_enterprise"' in content
