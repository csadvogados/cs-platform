from datetime import datetime, timedelta, timezone
import uuid

from app.db.session import SessionLocal
from app.models.crm import Lead, LeadProposal


def auth(token):
    return {"Authorization": f"Bearer {token}"}


def create_lead(client, token, name="Lead Automação"):
    catalog = client.get("/api/v1/leads/catalogs", headers=auth(token)).json()
    response = client.post("/api/v1/leads", headers=auth(token), json={
        "full_name": name,
        "email": "automacao@example.com",
        "source_id": catalog["sources"][0]["id"],
        "service_type_id": catalog["services"][0]["id"],
    })
    assert response.status_code == 201, response.text
    return response.json()


def test_lead_task_creates_internal_notification(client, token):
    lead = create_lead(client, token)
    due_at = datetime.now(timezone.utc) + timedelta(hours=4)
    response = client.post(f"/api/v1/leads/{lead['id']}/tasks", headers=auth(token), json={
        "description": "Retornar pelo WhatsApp", "due_at": due_at.isoformat(),
    })
    assert response.status_code == 201, response.text

    notifications = client.get("/api/v1/notifications?notification_type=lead", headers=auth(token))
    assert notifications.status_code == 200, notifications.text
    item = next(row for row in notifications.json()["items"] if row["target_filter"] == f"lead:{lead['id']}")
    assert item["title"] == "Próxima ação do lead se aproxima"
    assert "Retornar pelo WhatsApp" in item["message"]
    dashboard = client.get("/api/v1/leads/analytics/dashboard", headers=auth(token)).json()
    assert dashboard["leads_without_next_action"] == 0


def test_expired_proposal_is_updated_and_notified_once(client, token):
    lead = create_lead(client, token)
    yesterday = (datetime.now(timezone.utc) - timedelta(days=1)).date()
    response = client.post(f"/api/v1/leads/{lead['id']}/proposals", headers=auth(token), json={
        "fixed_value": 1500, "valid_until": yesterday.isoformat(), "status": "ENVIADA",
    })
    assert response.status_code == 201, response.text
    proposal_id = response.json()["id"]

    first = client.get("/api/v1/notifications?notification_type=lead", headers=auth(token))
    second = client.get("/api/v1/notifications?notification_type=lead", headers=auth(token))
    assert first.status_code == 200 and second.status_code == 200
    matching = [row for row in second.json()["items"] if row["title"] == "Proposta expirada"]
    assert len(matching) == 1
    with SessionLocal() as db:
        assert db.get(LeadProposal, uuid.UUID(proposal_id)).status == "EXPIRADA"


def test_unattended_lead_without_future_task_is_notified(client, token):
    lead = create_lead(client, token, "Lead sem retorno")
    with SessionLocal() as db:
        model = db.get(Lead, uuid.UUID(lead["id"]))
        model.updated_at = datetime.now(timezone.utc) - timedelta(days=4)
        db.commit()

    response = client.get("/api/v1/notifications?notification_type=lead", headers=auth(token))
    assert response.status_code == 200, response.text
    assert any(row["title"] == "Lead sem próxima ação" and "Lead sem retorno" in row["message"] for row in response.json()["items"])
    dashboard = client.get("/api/v1/leads/analytics/dashboard", headers=auth(token)).json()
    assert dashboard["leads_without_next_action"] == 1


def test_first_interaction_advances_new_lead_and_task_can_be_completed(client, token):
    lead = create_lead(client, token)
    interaction = client.post(f"/api/v1/leads/{lead['id']}/interactions", headers=auth(token), json={
        "interaction_type": "WHATSAPP", "description": "Cliente respondeu",
        "occurred_at": datetime.now(timezone.utc).isoformat(),
    })
    assert interaction.status_code == 201, interaction.text
    assert client.get(f"/api/v1/leads/{lead['id']}", headers=auth(token)).json()["status"] == "CONTATADO"

    task = client.post(f"/api/v1/leads/{lead['id']}/tasks", headers=auth(token), json={
        "description": "Enviar documentos", "due_at": (datetime.now(timezone.utc) + timedelta(days=1)).isoformat(),
    }).json()
    completed = client.patch(f"/api/v1/leads/{lead['id']}/tasks/{task['id']}/complete", headers=auth(token))
    assert completed.status_code == 200, completed.text
    assert completed.json()["status"] == "CONCLUIDA"


def test_proposal_status_can_be_decided_after_creation(client, token):
    lead = create_lead(client, token)
    proposal = client.post(f"/api/v1/leads/{lead['id']}/proposals", headers=auth(token), json={
        "fixed_value": 2500, "status": "ENVIADA",
    })
    assert proposal.status_code == 201, proposal.text
    updated = client.patch(f"/api/v1/leads/{lead['id']}/proposals/{proposal.json()['id']}", headers=auth(token), json={"status": "ACEITA"})
    assert updated.status_code == 200, updated.text
    assert updated.json()["status"] == "ACEITA"


def test_user_without_commercial_access_does_not_receive_lead_details(client, token):
    lead = create_lead(client, token, "Lead restrito")
    task = client.post(f"/api/v1/leads/{lead['id']}/tasks", headers=auth(token), json={
        "description": "Contato confidencial", "due_at": (datetime.now(timezone.utc) + timedelta(hours=2)).isoformat(),
    })
    assert task.status_code == 201, task.text
    created = client.post("/api/v1/users", headers=auth(token), json={
        "full_name": "Financeiro Automação", "email": "financeiro-automacao@example.com",
        "password": "SecurePass123!", "role": "financeiro",
    })
    assert created.status_code == 201, created.text
    login = client.post("/api/v1/auth/token", data={"username": "financeiro-automacao@example.com", "password": "SecurePass123!"})
    assert login.status_code == 200, login.text
    page = client.get("/api/v1/notifications?notification_type=lead", headers=auth(login.json()["access_token"]))
    assert page.status_code == 200, page.text
    assert page.json()["items"] == []
