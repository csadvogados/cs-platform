from datetime import datetime, timedelta, timezone
import uuid
from pathlib import Path

from app.db.session import SessionLocal
from app.models.recovery import RecoveryCase


def auth(token):
    return {"Authorization": f"Bearer {token}"}


def create_open_judicial_process(client, token):
    customer = client.post("/api/v1/clients", headers=auth(token), json={
        "full_name": "Cliente Encerramento Judicial", "cpf": "52998224725"
    }).json()
    case = client.post("/api/v1/recovery-cases", headers=auth(token), json={"client_id": customer["id"]}).json()
    with SessionLocal() as db:
        model = db.get(RecoveryCase, uuid.UUID(case["id"]))
        model.status = "judicialized"
        model.stage = "closed"
        db.commit()
    process = client.put(f"/api/v1/recovery-cases/{case['id']}/judicial-process", headers=auth(token), json={
        "process_number": "5001234-56.2026.8.26.0100", "court": "TJSP",
        "next_deadline": (datetime.now(timezone.utc) + timedelta(days=1)).isoformat(),
        "status": "decision_issued",
    }).json()
    return case, process


def test_controlled_closure_records_outcome_and_removes_deadline(client, token):
    case, process = create_open_judicial_process(client, token)
    response = client.post(f"/api/v1/recovery-cases/{case['id']}/judicial-process/close", headers=auth(token), json={
        "outcome": "favorable", "closed_at": datetime.now(timezone.utc).isoformat(),
        "reason": "Sentença favorável com trânsito em julgado.", "version": process["version"],
    })
    assert response.status_code == 200, response.text
    closed = response.json()
    assert closed["status"] == "closed"
    assert closed["outcome"] == "favorable"
    assert closed["next_deadline"] is None
    assert closed["events"][0]["title"] == "Processo judicial encerrado"
    agenda = client.get("/api/v1/financial/operational-agenda", headers=auth(token)).json()
    assert all(item["kind"] != "judicial_deadline" for item in agenda["items"])


def test_closure_requires_dedicated_action_and_cannot_repeat(client, token):
    case, process = create_open_judicial_process(client, token)
    direct = client.put(f"/api/v1/recovery-cases/{case['id']}/judicial-process", headers=auth(token), json={
        "process_number": process["process_number"], "court": process["court"],
        "status": "closed", "version": process["version"],
    })
    assert direct.status_code == 422
    payload = {"outcome": "settlement", "closed_at": datetime.now(timezone.utc).isoformat(),
               "reason": "Acordo homologado judicialmente.", "version": process["version"]}
    first = client.post(f"/api/v1/recovery-cases/{case['id']}/judicial-process/close", headers=auth(token), json=payload)
    assert first.status_code == 200
    payload["version"] = first.json()["version"]
    repeated = client.post(f"/api/v1/recovery-cases/{case['id']}/judicial-process/close", headers=auth(token), json=payload)
    assert repeated.status_code == 409


def test_only_closure_reason_can_be_corrected_after_closing(client, token):
    case, process = create_open_judicial_process(client, token)
    closed = client.post(f"/api/v1/recovery-cases/{case['id']}/judicial-process/close", headers=auth(token), json={
        "outcome": "dismissed", "closed_at": datetime.now(timezone.utc).isoformat(),
        "reason": "Texto inicial a corrigir.", "version": process["version"],
    }).json()
    corrected = client.patch(
        f"/api/v1/recovery-cases/{case['id']}/judicial-process/closure-reason",
        headers=auth(token),
        json={"reason": "Extinto sem resolução do mérito por ausência de pressuposto processual.", "version": closed["version"]},
    )
    assert corrected.status_code == 200, corrected.text
    result = corrected.json()
    assert result["closure_reason"].startswith("Extinto sem resolução")
    assert result["outcome"] == closed["outcome"]
    assert result["closed_at"] == closed["closed_at"]
    assert result["status"] == "closed"
    assert result["version"] == closed["version"] + 1
    assert result["events"][0]["title"] == "Motivo do encerramento corrigido"


def test_closure_options_can_be_reopened_and_corrected(client, token):
    case, process = create_open_judicial_process(client, token)
    closed = client.post(f"/api/v1/recovery-cases/{case['id']}/judicial-process/close", headers=auth(token), json={
        "outcome": "dismissed", "closed_at": datetime.now(timezone.utc).isoformat(),
        "reason": "Informação inicial incorreta.", "version": process["version"],
    }).json()
    corrected_at = datetime.now(timezone.utc)
    corrected = client.patch(
        f"/api/v1/recovery-cases/{case['id']}/judicial-process/closure",
        headers=auth(token),
        json={"outcome": "unfavorable", "closed_at": corrected_at.isoformat(),
              "reason": "Pedido julgado improcedente.", "version": closed["version"]},
    )
    assert corrected.status_code == 200, corrected.text
    result = corrected.json()
    assert result["outcome"] == "unfavorable"
    assert result["closure_reason"] == "Pedido julgado improcedente."
    assert result["status"] == "closed"
    assert result["events"][0]["title"] == "Dados do encerramento corrigidos"


def test_frontend_exposes_controlled_closure():
    frontend = Path(__file__).parents[2] / "frontend"
    index = (frontend / "index.html").read_text(encoding="utf-8")
    app = (frontend / "assets" / "app.js").read_text(encoding="utf-8")
    assert 'id="judicial-closure-dialog"' in index
    assert 'id="close-judicial-process"' in index
    assert 'id="edit-judicial-closure"' in index
    assert 'id="judicial-closure-title"' in index
    assert "/judicial-process/${path}" in app
    assert 'editing ? "closure" : "close"' in app
    assert "5.34.0-judicial-closure" in index
