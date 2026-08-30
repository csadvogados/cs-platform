from pathlib import Path

from alembic.config import Config
from alembic.script import ScriptDirectory


ROOT = Path(__file__).parents[2]


def test_database_has_single_migration_head():
    config = Config(str(ROOT / "backend" / "alembic.ini"))
    config.set_main_option("script_location", str(ROOT / "backend" / "alembic"))
    heads = ScriptDirectory.from_config(config).get_heads()
    assert heads == ["0024_judicial_closure"]


def test_production_endpoints_are_in_openapi(client, token):
    paths = client.get("/openapi.json").json()["paths"]
    assert "/api/v1/judicial-reports/summary" in paths
    assert "/api/v1/judicial-reports/summary.csv" in paths
    assert "/api/v1/recovery-cases/{case_id}/judicial-process/close" in paths
    assert "/api/v1/recovery-cases/{case_id}/judicial-process/deadline/complete" in paths


def test_health_and_security_headers(client):
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.headers.get("x-content-type-options") == "nosniff"
    assert response.headers.get("x-frame-options")


def test_production_checklist_exists_and_frontend_is_versioned():
    checklist = (ROOT / "PRODUCTION_CHECKLIST.md").read_text(encoding="utf-8")
    index = (ROOT / "frontend" / "index.html").read_text(encoding="utf-8")
    assert "Rollback" in checklist
    assert "0024" in checklist
    assert "5.37.0-production-ready" in index
