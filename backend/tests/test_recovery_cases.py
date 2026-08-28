import uuid

from sqlalchemy import select

from app.db.session import SessionLocal
from app.models.audit import AuditEvent
from app.models.organization import Organization
from app.models.recovery import RecoveryCase


def auth(token):
    return {"Authorization": f"Bearer {token}"}


def create_client(client, token, cpf="12345678901"):
    response = client.post("/api/v1/clients", headers=auth(token), json={
        "full_name": "Cliente Recupera", "cpf": cpf, "person_natural": True,
    })
    assert response.status_code == 201, response.text
    return response.json()


def test_recovery_case_lifecycle_and_audit(client, token):
    customer = create_client(client, token)
    created = client.post("/api/v1/recovery-cases", headers=auth(token), json={
        "client_id": customer["id"], "notes": "Triagem inicial",
    })
    assert created.status_code == 201, created.text
    case = created.json()
    assert case["status"] == "draft"
    assert case["stage"] == "intake"
    assert case["version"] == 1
    assert case["case_number"].startswith("REC-")

    transitioned = client.post(
        f"/api/v1/recovery-cases/{case['id']}/transitions", headers=auth(token),
        json={"status": "active", "stage": "documents", "version": 1},
    )
    assert transitioned.status_code == 200, transitioned.text
    assert transitioned.json()["version"] == 2
    assert transitioned.json()["opened_at"] is not None

    page = client.get("/api/v1/recovery-cases?status=active", headers=auth(token))
    assert page.status_code == 200
    assert page.json()["total"] == 1

    with SessionLocal() as db:
        actions = list(db.scalars(select(AuditEvent).where(AuditEvent.entity_type == "recovery_case")))
        assert {item.action for item in actions} == {"create", "transition"}


def test_recovery_case_rejects_stale_version_and_invalid_transition(client, token):
    customer = create_client(client, token, "98765432100")
    case = client.post("/api/v1/recovery-cases", headers=auth(token), json={"client_id": customer["id"]}).json()

    invalid = client.post(
        f"/api/v1/recovery-cases/{case['id']}/transitions", headers=auth(token),
        json={"status": "resolved", "version": 1},
    )
    assert invalid.status_code == 409

    updated = client.patch(
        f"/api/v1/recovery-cases/{case['id']}", headers=auth(token),
        json={"notes": "Atualizado", "version": 1},
    )
    assert updated.status_code == 200
    stale = client.patch(
        f"/api/v1/recovery-cases/{case['id']}", headers=auth(token),
        json={"notes": "Conflito", "version": 1},
    )
    assert stale.status_code == 409


def test_recovery_case_hides_other_tenant(client, token):
    customer = create_client(client, token, "11144477735")
    case = client.post("/api/v1/recovery-cases", headers=auth(token), json={"client_id": customer["id"]}).json()
    with SessionLocal() as db:
        other = Organization(legal_name="Outro tenant", trade_name="Outro")
        db.add(other); db.flush()
        db.execute(RecoveryCase.__table__.update().where(RecoveryCase.id == uuid.UUID(case["id"])).values(organization_id=other.id))
        db.commit()
    response = client.get(f"/api/v1/recovery-cases/{case['id']}", headers=auth(token))
    assert response.status_code == 404
