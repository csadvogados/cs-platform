import uuid

from sqlalchemy import select

from app.db.session import SessionLocal
from app.models.audit import AuditEvent
from app.models.client import Client


def auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def create_client(client, token, *, name="Cliente Sprint Um", cpf="52998224725"):
    response = client.post(
        "/api/v1/clients",
        headers=auth(token),
        json={"full_name": name, "cpf": cpf, "phone": "13999990000"},
    )
    assert response.status_code == 201, response.text
    return response.json()


def test_dashboard_summary_is_organization_scoped(client, token):
    create_client(client, token)

    response = client.get("/api/v1/dashboard/summary", headers=auth(token))

    assert response.status_code == 200
    assert response.json() == {
        "clients_total": 1,
        "clients_active": 1,
        "clients_archived": 0,
        "users_active": 1,
    }


def test_client_delete_soft_archives_and_hides_by_default(client, token):
    created = create_client(client, token)

    response = client.delete(f"/api/v1/clients/{created['id']}", headers=auth(token))
    assert response.status_code == 204

    assert client.get(f"/api/v1/clients/{created['id']}", headers=auth(token)).status_code == 404
    assert client.get("/api/v1/clients", headers=auth(token)).json() == []

    archived = client.get(
        "/api/v1/clients?include_archived=true", headers=auth(token)
    ).json()
    assert len(archived) == 1
    assert archived[0]["archived_at"] is not None

    with SessionLocal() as db:
        stored = db.scalar(select(Client).where(Client.id == uuid.UUID(created["id"])))
        assert stored is not None
        assert stored.archived_at is not None
        audit = db.scalar(
            select(AuditEvent).where(
                AuditEvent.entity_id == stored.id,
                AuditEvent.action == "archive",
            )
        )
        assert audit is not None


def test_dashboard_counts_archived_clients(client, token):
    created = create_client(client, token)
    client.delete(f"/api/v1/clients/{created['id']}", headers=auth(token))

    response = client.get("/api/v1/dashboard/summary", headers=auth(token))

    assert response.status_code == 200
    assert response.json()["clients_total"] == 1
    assert response.json()["clients_active"] == 0
    assert response.json()["clients_archived"] == 1

<<<<<<< HEAD

def test_archived_only_filter_and_restore(client, token):
    created = create_client(client, token)
    client.delete(f"/api/v1/clients/{created['id']}", headers=auth(token))
    archived = client.get("/api/v1/clients/page?archived_only=true", headers=auth(token))
    assert archived.status_code == 200
    assert archived.json()["total"] == 1
    restored = client.post(f"/api/v1/clients/{created['id']}/restore", headers=auth(token))
    assert restored.status_code == 200
    assert restored.json()["archived_at"] is None
    assert client.get("/api/v1/clients/page?archived_only=true", headers=auth(token)).json()["total"] == 0
    with SessionLocal() as db:
        audit = db.scalar(select(AuditEvent).where(AuditEvent.entity_id == uuid.UUID(created["id"]), AuditEvent.action == "restore"))
        assert audit is not None


def test_duplicate_cpf_has_clear_message(client, token):
    create_client(client, token)
    response = client.post("/api/v1/clients", headers=auth(token), json={"full_name": "CPF repetido", "cpf": "52998224725"})
    assert response.status_code == 409
    assert response.json()["error"]["message"] == "CPF já cadastrado nesta organização"
=======
>>>>>>> 6a81ade2942ff2fbe866de1c6f119b0854c6fc9b
