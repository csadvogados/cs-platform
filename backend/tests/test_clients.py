def test_create_list_update_client(client, token):
    headers={"Authorization":f"Bearer {token}"}
    payload={"full_name":"Maria da Silva","cpf":"12345678901","phone":"13999990000","city":"Peruíbe","state":"sp","person_natural":True,"good_faith_declared":True}
    created=client.post("/api/v1/clients",json=payload,headers=headers)
    assert created.status_code == 201, created.text
    cid=created.json()["id"]
    assert created.json()["state"] == "SP"
    listed=client.get("/api/v1/clients?q=Maria",headers=headers)
    assert listed.status_code == 200 and len(listed.json()) == 1
    updated=client.patch(f"/api/v1/clients/{cid}",json={"status":"contracted"},headers=headers)
    assert updated.status_code == 200
    assert updated.json()["status"] == "contracted"

def test_duplicate_cpf(client, token):
    headers={"Authorization":f"Bearer {token}"}
    payload={"full_name":"Cliente Um","cpf":"98765432100"}
    assert client.post("/api/v1/clients",json=payload,headers=headers).status_code == 201
    payload["full_name"]="Cliente Dois"
    assert client.post("/api/v1/clients",json=payload,headers=headers).status_code == 409


def test_client_profile_returns_unified_empty_summary(client, token):
    headers = {"Authorization": f"Bearer {token}"}
    created = client.post(
        "/api/v1/clients",
        json={"full_name": "Cliente Perfil", "cpf": "52998224725"},
        headers=headers,
    )
    assert created.status_code == 201, created.text

    response = client.get(
        f"/api/v1/clients/{created.json()['id']}/profile",
        headers=headers,
    )
    assert response.status_code == 200, response.text
    assert response.json() == {
        "lead": None,
        "contract": None,
        "recovery_case": None,
        "next_action": None,
        "latest_diagnosis": None,
        "document_count": 0,
        "negotiation_count": 0,
        "agreement_count": 0,
        "timeline": [],
    }


def test_profile_document_history_excludes_deleted_and_other_clients(client, token):
    import uuid
    from datetime import datetime, timezone
    from app.db.session import SessionLocal
    from app.models.client import Client
    from app.models.document import ClientDocument

    headers = {"Authorization": f"Bearer {token}"}
    ids = []
    for name, cpf in [("Perfil Histórico", "12345678901"), ("Outro Cliente", "98765432100")]:
        response = client.post("/api/v1/clients", json={"full_name": name, "cpf": cpf}, headers=headers)
        assert response.status_code == 201, response.text
        ids.append(uuid.UUID(response.json()["id"]))
    with SessionLocal() as db:
        org = db.get(Client, ids[0]).organization_id
        for cid, filename, deleted, day in [
            (ids[0], "antigo.pdf", False, 1),
            (ids[0], "recente.pdf", False, 2),
            (ids[0], "excluido.pdf", True, 3),
            (ids[1], "outro.pdf", False, 4),
        ]:
            db.add(ClientDocument(organization_id=org, client_id=cid, category="other",
                filename=filename, content_type="application/pdf", size_bytes=6, content=b"secret",
                created_at=datetime(2026, 1, day, tzinfo=timezone.utc),
                deleted_at=datetime.now(timezone.utc) if deleted else None))
        db.commit()
    response = client.get(f"/api/v1/clients/{ids[0]}/profile", headers=headers)
    assert response.status_code == 200, response.text
    assert response.json()["document_count"] == 2
    assert [item["title"] for item in response.json()["timeline"]] == [
        "Documento: recente.pdf", "Documento: antigo.pdf"]
    assert "secret" not in response.text
