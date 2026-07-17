from pathlib import Path

from app.core.constants import APP_VERSION


BACKEND = Path(__file__).resolve().parents[1]


def test_release_version_is_v542():
    assert APP_VERSION == "5.4.2"


def test_docker_entrypoint_uses_runtime_port_and_runs_migrations():
    content = (BACKEND / "docker-entrypoint.sh").read_text(encoding="utf-8")
    assert 'PORT="${PORT:-8000}"' in content
    assert "python -m alembic -c /app/alembic.ini upgrade head" in content
    assert "0006_crm_stabilization.py" in content
    assert "exec python -m uvicorn" in content
    assert '--port "$PORT"' in content


def test_railway_uses_single_entrypoint_without_predeploy_migration():
    content = (BACKEND / "railway.json").read_text(encoding="utf-8")
    assert '"startCommand": "/app/docker-entrypoint.sh"' in content
    assert '"preDeployCommand"' not in content
    assert '"healthcheckPath": "/api/v1/health"' in content
    assert '"healthcheckTimeout": 300' in content


def test_dockerfile_uses_cmd_not_entrypoint_to_avoid_override_recursion():
    content = (BACKEND / "Dockerfile").read_text(encoding="utf-8")
    assert 'CMD ["/app/docker-entrypoint.sh"]' in content
    assert "ENTRYPOINT" not in content
    assert "test -f /app/alembic/versions/0006_crm_stabilization.py" in content


def test_required_migration_is_packaged():
    migration = BACKEND / "alembic" / "versions" / "0006_crm_stabilization.py"
    assert migration.exists()
    content = migration.read_text(encoding="utf-8")
    assert 'revision = "0006_crm_stabilization"' in content
    assert 'down_revision = "0005_crm_enterprise"' in content
