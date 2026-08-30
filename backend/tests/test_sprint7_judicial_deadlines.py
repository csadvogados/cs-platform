from datetime import datetime, timedelta, timezone
import uuid
from pathlib import Path

from app.db.session import SessionLocal
from app.models.recovery import JudicialProcess, RecoveryCase


def auth(token):
    return {"Authorization": f"Bearer {token}"}


def create_judicial_deadline(client, token, due_at):
    customer = client.post("/api/v1/clients", headers=auth(token), json={
        "full_name": "Cliente Prazo Judicial", "cpf": "52998224725"
    }).json()
    case = client.post("/api/v1/recovery-cases", headers=auth(token), json={"client_id": customer["id"]}).json()
    with SessionLocal() as db:
        model = db.get(RecoveryCase, uuid.UUID(case["id"]))
        model.status = "judicialized"
        model.stage = "closed"
        db.commit()
    process = client.put(f"/api/v1/recovery-cases/{case['id']}/judicial-process", headers=auth(token), json={
        "process_number": "3001234-56.2026.8.26.0100", "court": "TJSP",
        "next_deadline": due_at.isoformat(), "status": "awaiting_decision",
    })
    assert process.status_code == 200, process.text
    return customer, case, process.json()


def test_judicial_deadline_appears_in_agenda_and_notification(client, token):
    due_at = datetime.now(timezone.utc) + timedelta(days=1)
    customer, case, process = create_judicial_deadline(client, token, due_at)
    agenda = client.get("/api/v1/financial/operational-agenda", headers=auth(token))
    assert agenda.status_code == 200, agenda.text
    item = next(row for row in agenda.json()["items"] if row["kind"] == "judicial_deadline")
    assert item["client_id"] == customer["id"]
    assert item["target_filter"] == f"judicial:{case['id']}"
    notifications = client.get("/api/v1/notifications?notification_type=judicial", headers=auth(token))
    assert notifications.status_code == 200, notifications.text
    assert notifications.json()["items"][0]["notification_type"] == "judicial"


def test_overdue_judicial_deadline_is_critical_alert(client, token):
    create_judicial_deadline(client, token, datetime.now(timezone.utc) - timedelta(days=1))
    alerts = client.get("/api/v1/financial/operational-alerts", headers=auth(token))
    assert alerts.status_code == 200, alerts.text
    judicial = next(row for row in alerts.json()["items"] if row["key"] == "overdue_judicial")
    assert judicial["severity"] == "critical"
    assert judicial["target_view"] == "agenda"


def test_frontend_has_judicial_deadline_filters():
    frontend = Path(__file__).parents[2] / "frontend"
    index = (frontend / "index.html").read_text(encoding="utf-8")
    app = (frontend / "assets" / "app.js").read_text(encoding="utf-8")
    assert 'value="judicial_deadline"' in index
    assert 'name="judicial_enabled"' in index
    assert 'agenda-judicial-count' in app
    assert 'item.kind === "judicial_deadline"' in app
