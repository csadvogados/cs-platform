from datetime import datetime, timedelta, timezone


def auth(token):
    return {"Authorization": f"Bearer {token}"}


def create_client(client, token, *, cpf="12345678901", name="Maria Lead"):
    response = client.post(
        "/api/v1/clients",
        headers=auth(token),
        json={
            "full_name": name,
            "cpf": cpf,
            "email": "lead@example.com",
            "phone": "13999990000",
            "city": "Peruíbe",
            "state": "SP",
        },
    )
    assert response.status_code == 201, response.text
    return response.json()


def create_opportunity(client, token, client_id, **overrides):
    payload = {
        "client_id": client_id,
        "title": "CS Recupera — diagnóstico",
        "source": "Instagram",
        "service": "CS Recupera",
        "estimated_value": 1500,
        "probability": 30,
        "next_contact_at": (datetime.now(timezone.utc) + timedelta(days=1)).isoformat(),
    }
    payload.update(overrides)
    response = client.post(
        "/api/v1/crm/opportunities",
        headers=auth(token),
        json=payload,
    )
    assert response.status_code == 201, response.text
    return response.json()


def test_cs_captacao_pipeline_history_detail_and_conversion(client, token):
    headers = auth(token)
    lead = create_client(client, token)
    opportunity = create_opportunity(client, token, lead["id"])
    opportunity_id = opportunity["id"]

    assert opportunity["stage"] == "new"
    assert opportunity["source"] == "Instagram"
    assert opportunity["service"] == "CS Recupera"

    pipeline = client.get("/api/v1/crm/pipeline?source=Instagram", headers=headers)
    assert pipeline.status_code == 200, pipeline.text
    columns = {column["stage"]: column for column in pipeline.json()}
    assert columns["new"]["label"] == "NOVO"
    assert columns["new"]["count"] == 1
    card = columns["new"]["items"][0]
    assert card["client_name"] == "Maria Lead"
    assert card["service"] == "CS Recupera"
    assert card["source"] == "Instagram"
    assert card["next_contact_at"] is not None

    expected_history = ["new"]
    for stage, note in [
        ("contacted", "Contato por WhatsApp"),
        ("qualified", "Lead elegível"),
        ("proposal", "Proposta apresentada"),
    ]:
        changed = client.post(
            f"/api/v1/crm/opportunities/{opportunity_id}/stage",
            headers=headers,
            json={"stage": stage, "note": note},
        )
        assert changed.status_code == 200, changed.text
        assert changed.json()["stage"] == stage
        expected_history.append(stage)

    interaction = client.post(
        "/api/v1/crm/interactions",
        headers=headers,
        json={
            "client_id": lead["id"],
            "opportunity_id": opportunity_id,
            "interaction_type": "message",
            "subject": "Envio da proposta",
            "occurred_at": datetime.now(timezone.utc).isoformat(),
        },
    )
    assert interaction.status_code == 201, interaction.text

    task = client.post(
        "/api/v1/crm/tasks",
        headers=headers,
        json={
            "opportunity_id": opportunity_id,
            "title": "Confirmar aceite",
            "priority": "high",
            "due_at": (datetime.now(timezone.utc) + timedelta(hours=4)).isoformat(),
        },
    )
    assert task.status_code == 201, task.text
    assert task.json()["client_id"] == lead["id"]

    history = client.get(
        f"/api/v1/crm/opportunities/{opportunity_id}/history",
        headers=headers,
    )
    assert history.status_code == 200, history.text
    assert [item["to_stage"] for item in history.json()] == expected_history

    detail = client.get(
        f"/api/v1/crm/opportunities/{opportunity_id}/detail",
        headers=headers,
    )
    assert detail.status_code == 200, detail.text
    assert detail.json()["client"]["id"] == lead["id"]
    assert len(detail.json()["interactions"]) == 1
    assert len(detail.json()["tasks"]) == 1
    assert detail.json()["case"] is None

    converted = client.post(
        f"/api/v1/crm/opportunities/{opportunity_id}/convert",
        headers=headers,
        json={"create_case": True, "case_status": "triage", "note": "Contrato aceito"},
    )
    assert converted.status_code == 200, converted.text
    body = converted.json()
    assert body["opportunity"]["stage"] == "converted"
    assert body["client"]["status"] == "contracted"
    assert body["case"] is not None
    assert body["case"]["service"] == "CS Recupera"
    assert body["case"]["status"] == "triage"
    assert body["case"]["opportunity_id"] == opportunity_id

    # Conversão é idempotente: não cria um segundo caso.
    converted_again = client.post(
        f"/api/v1/crm/opportunities/{opportunity_id}/convert",
        headers=headers,
        json={"create_case": True},
    )
    assert converted_again.status_code == 200, converted_again.text
    assert converted_again.json()["case"]["id"] == body["case"]["id"]

    invalid_reopen = client.post(
        f"/api/v1/crm/opportunities/{opportunity_id}/stage",
        headers=headers,
        json={"stage": "qualified"},
    )
    assert invalid_reopen.status_code == 422


def test_cs_captacao_dashboard_and_filters(client, token):
    headers = auth(token)
    lead_a = create_client(client, token, cpf="22345678901", name="Lead Instagram")
    lead_b = create_client(client, token, cpf="32345678901", name="Lead Indicação")
    lead_c = create_client(client, token, cpf="42345678901", name="Lead Perdido")

    proposal = create_opportunity(
        client,
        token,
        lead_a["id"],
        title="Proposta Instagram",
        source="Instagram",
        service="CS Recupera",
        stage="proposal",
        estimated_value=1800,
        probability=70,
    )
    converted = create_opportunity(
        client,
        token,
        lead_b["id"],
        title="Contrato por indicação",
        source="Indicação",
        service="CS Recupera",
        stage="qualified",
        estimated_value=2400,
        probability=90,
    )
    converted_response = client.post(
        f"/api/v1/crm/opportunities/{converted['id']}/convert",
        headers=headers,
        json={"create_case": True},
    )
    assert converted_response.status_code == 200, converted_response.text

    lost = create_opportunity(
        client,
        token,
        lead_c["id"],
        title="Sem interesse",
        source="Instagram",
        service="CS Recupera",
        stage="qualified",
        estimated_value=900,
        probability=20,
    )
    lost_response = client.post(
        f"/api/v1/crm/opportunities/{lost['id']}/stage",
        headers=headers,
        json={"stage": "lost", "lost_reason": "Sem interesse"},
    )
    assert lost_response.status_code == 200, lost_response.text

    dashboard = client.get("/api/v1/crm/dashboard", headers=headers)
    assert dashboard.status_code == 200, dashboard.text
    data = dashboard.json()
    assert data["leads_new"] == 3
    assert data["open_proposals"] == 1
    assert data["leads_converted"] == 1
    assert data["leads_lost"] == 1
    assert data["conversion_rate"] == 50.0
    assert data["estimated_proposal_revenue"] == 1800.0
    assert data["contracted_revenue"] == 2400.0

    instagram = client.get(
        "/api/v1/crm/dashboard?source=Instagram&service=CS%20Recupera",
        headers=headers,
    )
    assert instagram.status_code == 200, instagram.text
    filtered = instagram.json()
    assert filtered["leads_new"] == 2
    assert filtered["open_proposals"] == 1
    assert filtered["leads_lost"] == 1
    assert filtered["leads_converted"] == 0

    listed = client.get(
        "/api/v1/crm/opportunities?source=Instagram&service=CS%20Recupera",
        headers=headers,
    )
    assert listed.status_code == 200, listed.text
    assert {item["id"] for item in listed.json()} == {proposal["id"], lost["id"]}
