from datetime import datetime, timedelta, timezone
import uuid
from pathlib import Path

from app.db.session import SessionLocal
from app.models.recovery import RecoveryCase


def auth(token):
    return {"Authorization": f"Bearer {token}"}


def create_process(client, token, cpf="39053344705"):
    customer = client.post("/api/v1/clients", headers=auth(token), json={"full_name": "Cliente Relatório Judicial", "cpf": cpf}).json()
    case = client.post("/api/v1/recovery-cases", headers=auth(token), json={"client_id": customer["id"]}).json()
    with SessionLocal() as db:
        model = db.get(RecoveryCase, uuid.UUID(case["id"]))
        model.status = "judicialized"
        model.stage = "closed"
        db.commit()
    process = client.put(f"/api/v1/recovery-cases/{case['id']}/judicial-process", headers=auth(token), json={
        "process_number": "1001234-56.2026.8.26.0100", "court": "TJSP",
        "filed_at": (datetime.now(timezone.utc) - timedelta(days=30)).isoformat(),
        "next_deadline": (datetime.now(timezone.utc) - timedelta(days=1)).isoformat(),
        "status": "decision_issued",
    }).json()
    return case, process


def test_judicial_summary_and_csv_export(client, token):
    case, process = create_process(client, token)
    summary = client.get("/api/v1/judicial-reports/summary", headers=auth(token))
    assert summary.status_code == 200, summary.text
    assert summary.json()["total"] == 1
    assert summary.json()["active"] == 1
    assert summary.json()["overdue_deadlines"] == 1

    closed = client.post(f"/api/v1/recovery-cases/{case['id']}/judicial-process/close", headers=auth(token), json={
        "outcome": "favorable", "closed_at": datetime.now(timezone.utc).isoformat(),
        "reason": "Sentença favorável definitiva.", "version": process["version"],
    })
    assert closed.status_code == 200, closed.text
    report = client.get("/api/v1/judicial-reports/summary", headers=auth(token)).json()
    assert report["closed"] == 1
    assert report["favorable_rate"] == 100
    assert report["average_duration_days"] >= 29
    assert report["outcomes"][0]["label"] == "Favorável"

    exported = client.get("/api/v1/judicial-reports/summary.csv", headers=auth(token))
    assert exported.status_code == 200
    assert "text/csv" in exported.headers["content-type"]
    assert "Resultados favoráveis" in exported.content.decode("utf-8-sig")


def test_frontend_exposes_judicial_report():
    frontend = Path(__file__).parents[2] / "frontend"
    index = (frontend / "index.html").read_text(encoding="utf-8")
    app = (frontend / "assets" / "app.js").read_text(encoding="utf-8")
    assert 'id="judicial-report-panel"' in index
    assert 'id="judicial-report-export"' in index
    assert "/api/v1/judicial-reports/summary" in app
    assert "5.40.0-judicial-dossier" in index
