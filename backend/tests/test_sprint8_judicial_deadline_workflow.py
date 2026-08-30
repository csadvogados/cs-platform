from datetime import datetime, timedelta, timezone
import uuid
from pathlib import Path

from app.db.session import SessionLocal
from app.models.recovery import RecoveryCase


def auth(token):
    return {"Authorization": f"Bearer {token}"}


def create_process_with_deadline(client, token):
    customer = client.post("/api/v1/clients", headers=auth(token), json={
        "full_name": "Cliente Cumprimento Prazo", "cpf": "52998224725"
    }).json()
    case = client.post("/api/v1/recovery-cases", headers=auth(token), json={"client_id": customer["id"]}).json()
    with SessionLocal() as db:
        model = db.get(RecoveryCase, uuid.UUID(case["id"]))
        model.status = "judicialized"
        model.stage = "closed"
        db.commit()
    process = client.put(f"/api/v1/recovery-cases/{case['id']}/judicial-process", headers=auth(token), json={
        "process_number": "4001234-56.2026.8.26.0100", "court": "TJSP",
        "next_deadline": (datetime.now(timezone.utc) + timedelta(days=1)).isoformat(),
        "status": "awaiting_decision",
    }).json()
    return case, process


def test_complete_deadline_removes_it_from_agenda_and_records_history(client, token):
    case, process = create_process_with_deadline(client, token)
    completed = client.post(
        f"/api/v1/recovery-cases/{case['id']}/judicial-process/deadline/complete",
        headers=auth(token), json={
            "completed_at": datetime.now(timezone.utc).isoformat(),
            "notes": "Petição protocolada dentro do prazo.", "version": process["version"],
        },
    )
    assert completed.status_code == 200, completed.text
    result = completed.json()
    assert result["next_deadline"] is None
    assert result["version"] == process["version"] + 1
    assert result["events"][0]["title"] == "Prazo judicial concluído"
    agenda = client.get("/api/v1/financial/operational-agenda", headers=auth(token)).json()
    assert all(item["kind"] != "judicial_deadline" for item in agenda["items"])


def test_complete_deadline_rejects_stale_version_and_missing_deadline(client, token):
    case, process = create_process_with_deadline(client, token)
    stale = client.post(f"/api/v1/recovery-cases/{case['id']}/judicial-process/deadline/complete", headers=auth(token), json={
        "completed_at": datetime.now(timezone.utc).isoformat(), "version": 999,
    })
    assert stale.status_code == 409
    ok = client.post(f"/api/v1/recovery-cases/{case['id']}/judicial-process/deadline/complete", headers=auth(token), json={
        "completed_at": datetime.now(timezone.utc).isoformat(), "version": process["version"],
    })
    assert ok.status_code == 200
    repeated = client.post(f"/api/v1/recovery-cases/{case['id']}/judicial-process/deadline/complete", headers=auth(token), json={
        "completed_at": datetime.now(timezone.utc).isoformat(), "version": ok.json()["version"],
    })
    assert repeated.status_code == 409


def test_frontend_exposes_deadline_completion():
    frontend = Path(__file__).parents[2] / "frontend"
    index = (frontend / "index.html").read_text(encoding="utf-8")
    app = (frontend / "assets" / "app.js").read_text(encoding="utf-8")
    assert "5.33.0-judicial-deadline-workflow" in index
    assert "data-complete-judicial" in app
    assert "/deadline/complete" in app
