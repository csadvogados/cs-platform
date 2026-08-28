from datetime import datetime, timezone
import uuid

from app.db.session import SessionLocal
from app.models.recovery import RecoveryCase
from pathlib import Path


def auth(token):
    return {"Authorization": f"Bearer {token}"}


def judicial_case(client, token):
    customer = client.post("/api/v1/clients", headers=auth(token), json={"full_name": "Cliente Processo", "cpf": "52998224725"}).json()
    case = client.post("/api/v1/recovery-cases", headers=auth(token), json={"client_id": customer["id"]}).json()
    with SessionLocal() as db:
        model = db.get(RecoveryCase, uuid.UUID(case["id"]))
        model.status = "judicialized"
        model.stage = "closed"
        db.commit()
    return case["id"]


def test_judicial_process_and_history(client, token):
    case_id = judicial_case(client, token)
    created = client.put(f"/api/v1/recovery-cases/{case_id}/judicial-process", headers=auth(token), json={
        "process_number": "1001234-56.2026.8.26.0100", "court": "TJSP", "district": "São Paulo",
        "division": "1ª Vara Cível", "status": "filed", "filed_at": datetime.now(timezone.utc).isoformat(),
    })
    assert created.status_code == 200, created.text
    process = created.json()
    assert process["version"] == 1
    event = client.post(f"/api/v1/recovery-cases/{case_id}/judicial-process/events", headers=auth(token), json={
        "event_date": datetime.now(timezone.utc).isoformat(), "event_type": "movement",
        "title": "Conclusos para decisão", "description": "Movimentação registrada no tribunal.",
    })
    assert event.status_code == 201, event.text
    loaded = client.get(f"/api/v1/recovery-cases/{case_id}/judicial-process", headers=auth(token))
    assert loaded.status_code == 200
    assert loaded.json()["events"][0]["title"] == "Conclusos para decisão"


def test_process_requires_judicialized_case_and_version(client, token):
    customer = client.post("/api/v1/clients", headers=auth(token), json={"full_name": "Cliente Não Judicial", "cpf": "11144477735"}).json()
    case = client.post("/api/v1/recovery-cases", headers=auth(token), json={"client_id": customer["id"]}).json()
    blocked = client.put(f"/api/v1/recovery-cases/{case['id']}/judicial-process", headers=auth(token), json={
        "process_number": "1000000-00.2026.8.26.0100", "court": "TJSP"
    })
    assert blocked.status_code == 422

    case_id = judicial_case(client, token)
    created = client.put(f"/api/v1/recovery-cases/{case_id}/judicial-process", headers=auth(token), json={
        "process_number": "2001234-56.2026.8.26.0100", "court": "TJSP"
    }).json()
    conflict = client.put(f"/api/v1/recovery-cases/{case_id}/judicial-process", headers=auth(token), json={
        "process_number": created["process_number"], "court": "TJSP", "status": "appeal", "version": 999
    })
    assert conflict.status_code == 409


def test_frontend_exposes_judicial_tracking():
    frontend = Path(__file__).parents[2] / "frontend"
    index = (frontend / "index.html").read_text(encoding="utf-8")
    app = (frontend / "assets" / "app.js").read_text(encoding="utf-8")
    assert 'id="judicial-process-dialog"' in index
    assert 'id="judicial-event-form"' in index
    assert 'data-judicial-process' in app
    assert '/judicial-process/events' in app
