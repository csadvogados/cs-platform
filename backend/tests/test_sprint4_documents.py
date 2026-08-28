from sqlalchemy import select

from app.db.session import SessionLocal
from app.models.audit import AuditEvent


def auth(token):
    return {"Authorization": f"Bearer {token}"}


def create_client(client, token):
    response = client.post("/api/v1/clients", headers=auth(token), json={"full_name": "Cliente Documentos", "cpf": "52998224725"})
    assert response.status_code == 201, response.text
    return response.json()["id"]


def upload(client, token, client_id, category, filename="arquivo.pdf"):
    return client.post(
        f"/api/v1/documents/clients/{client_id}",
        headers=auth(token),
        data={"category": category},
        files={"file": (filename, b"%PDF-1.4 teste", "application/pdf")},
    )


def test_document_upload_download_validation_and_checklist(client, token):
    client_id = create_client(client, token)
    document_ids = []
    for category in ("identification", "income_proof", "residence_proof", "debt_statement"):
        response = upload(client, token, client_id, category, f"{category}.pdf")
        assert response.status_code == 201, response.text
        document_ids.append(response.json()["id"])

    listed = client.get(f"/api/v1/documents/clients/{client_id}", headers=auth(token))
    assert listed.status_code == 200
    assert len(listed.json()) == 4
    downloaded = client.get(f"/api/v1/documents/{document_ids[0]}/download", headers=auth(token))
    assert downloaded.status_code == 200
    assert downloaded.content.startswith(b"%PDF")

    pending = client.get(f"/api/v1/documents/clients/{client_id}/judicial-checklist", headers=auth(token)).json()
    assert pending["ready"] is False
    for document_id in document_ids:
        validated = client.post(f"/api/v1/documents/{document_id}/validation", headers=auth(token), json={"status": "validated", "notes": "Conferido"})
        assert validated.status_code == 200, validated.text

    checklist = client.get(f"/api/v1/documents/clients/{client_id}/judicial-checklist", headers=auth(token)).json()
    assert checklist["ready"] is True
    assert checklist["missing_categories"] == []
    with SessionLocal() as db:
        assert db.scalar(select(AuditEvent).where(AuditEvent.entity_type == "document", AuditEvent.action == "upload")) is not None
        assert db.scalar(select(AuditEvent).where(AuditEvent.entity_type == "document", AuditEvent.action == "validate")) is not None


def test_document_rejects_unsupported_file(client, token):
    client_id = create_client(client, token)
    response = client.post(
        f"/api/v1/documents/clients/{client_id}",
        headers=auth(token),
        data={"category": "other"},
        files={"file": ("arquivo.exe", b"invalid", "application/octet-stream")},
    )
    assert response.status_code == 422
