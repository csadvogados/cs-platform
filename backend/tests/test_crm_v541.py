from datetime import datetime, timedelta, timezone
from uuid import uuid4


def auth(token):
    return {"Authorization": f"Bearer {token}"}


def make_client(client, token, suffix="541"):
    response = client.post("/api/v1/clients", headers=auth(token), json={"full_name": f"Cliente {suffix}", "cpf": f"98765432{suffix[-3:]}", "email": f"{suffix}@example.com"})
    assert response.status_code == 201, response.text
    return response.json()["id"]


def test_crm_validation_and_crud(client, token):
    headers = auth(token)
    client_id = make_client(client, token)
    contact = client.post("/api/v1/crm/contacts", headers=headers, json={"client_id": client_id, "name": "  Maria   Silva  ", "email": "MARIA@EXAMPLE.COM"})
    assert contact.status_code == 201, contact.text
    contact_id = contact.json()["id"]
    assert contact.json()["name"] == "Maria Silva"
    assert contact.json()["email"] == "maria@example.com"
    updated = client.patch(f"/api/v1/crm/contacts/{contact_id}", headers=headers, json={"position": "Diretora"})
    assert updated.status_code == 200 and updated.json()["position"] == "Diretora"
    searched = client.get("/api/v1/crm/contacts?search=maria", headers=headers)
    assert searched.status_code == 200 and len(searched.json()) == 1

    opportunity = client.post("/api/v1/crm/opportunities", headers=headers, json={"client_id": client_id, "title": "Acordo empresarial", "estimated_value": 10000, "probability": 25})
    assert opportunity.status_code == 201, opportunity.text
    opportunity_id = opportunity.json()["id"]
    patched = client.patch(f"/api/v1/crm/opportunities/{opportunity_id}", headers=headers, json={"stage": "proposal", "probability": 50})
    assert patched.status_code == 200 and patched.json()["stage"] == "proposal"

    due = (datetime.now(timezone.utc) - timedelta(days=1)).isoformat()
    task = client.post("/api/v1/crm/tasks", headers=headers, json={"client_id": client_id, "opportunity_id": opportunity_id, "title": "Retornar ao cliente", "priority": "urgent", "due_at": due})
    assert task.status_code == 201, task.text
    task_id = task.json()["id"]
    overdue = client.get("/api/v1/crm/tasks?overdue_only=true", headers=headers)
    assert overdue.status_code == 200 and any(item["id"] == task_id for item in overdue.json())
    summary = client.get("/api/v1/crm/summary", headers=headers)
    assert summary.status_code == 200
    assert summary.json()["weighted_pipeline_value"] == 5000
    assert summary.json()["overdue_tasks"] == 1
    assert client.delete(f"/api/v1/crm/tasks/{task_id}", headers=headers).status_code == 204


def test_crm_rejects_invalid_values_and_foreign_references(client, token):
    headers = auth(token)
    client_id = make_client(client, token, "542")
    invalid_stage = client.post("/api/v1/crm/opportunities", headers=headers, json={"client_id": client_id, "title": "Teste", "stage": "unknown"})
    assert invalid_stage.status_code == 422
    invalid_priority = client.post("/api/v1/crm/tasks", headers=headers, json={"title": "Teste", "priority": "critical"})
    assert invalid_priority.status_code == 422
    foreign_client = client.post("/api/v1/crm/interactions", headers=headers, json={"client_id": str(uuid4()), "interaction_type": "call", "subject": "Teste", "occurred_at": datetime.now(timezone.utc).isoformat()})
    assert foreign_client.status_code == 422
