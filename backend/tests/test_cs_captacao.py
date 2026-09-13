def auth(token): return {"Authorization": f"Bearer {token}"}


def catalogs(client, token):
    response = client.get("/api/v1/leads/catalogs", headers=auth(token))
    assert response.status_code == 200, response.text
    return response.json()


def new_lead(client, token, *, cpf="52998224725"):
    data = catalogs(client, token)
    response = client.post("/api/v1/leads", headers=auth(token), json={
        "full_name": "Maria da Silva", "cpf": cpf, "whatsapp": "11999990000",
        "email": "maria@example.com", "source_id": data["sources"][0]["id"],
        "service_type_id": next(x["id"] for x in data["services"] if x["code"] == "CS_RECUPERA"),
        "priority": "ALTA"
    })
    assert response.status_code == 201, response.text
    return response.json()


def test_lead_crud_timeline_and_lost_reason(client, token):
    lead = new_lead(client, token)
    invalid = client.post(f"/api/v1/leads/{lead['id']}/status", headers=auth(token), json={"status": "PERDIDO"})
    assert invalid.status_code == 422
    changed = client.post(f"/api/v1/leads/{lead['id']}/status", headers=auth(token), json={"status": "CONTATADO"})
    assert changed.status_code == 200 and changed.json()["status"] == "CONTATADO"
    interaction = client.post(f"/api/v1/leads/{lead['id']}/interactions", headers=auth(token), json={"interaction_type":"WHATSAPP","description":"Cliente respondeu","occurred_at":"2026-09-10T12:00:00Z","next_action":"Enviar proposta","next_action_at":"2026-09-11T12:00:00Z"})
    assert interaction.status_code == 201, interaction.text
    timeline = client.get(f"/api/v1/leads/{lead['id']}/timeline", headers=auth(token))
    assert timeline.status_code == 200
    assert len(timeline.json()["interactions"]) == 3
    assert len(timeline.json()["tasks"]) == 1


def test_proposal_and_conversion_create_recovery_case(client, token):
    lead = new_lead(client, token)
    proposal = client.post(f"/api/v1/leads/{lead['id']}/proposals", headers=auth(token), json={"fixed_value":1500,"down_payment":125,"installments":12,"installment_value":125,"status":"ACEITA"})
    assert proposal.status_code == 201, proposal.text
    converted = client.post(f"/api/v1/leads/{lead['id']}/convert", headers=auth(token), json={"create_recovery_case":True})
    assert converted.status_code == 200, converted.text
    body = converted.json()
    assert body["lead"]["status"] == "CONVERTIDO"
    assert body["client_id"] and body["recovery_case_id"]
    dashboard = client.get("/api/v1/leads/analytics/dashboard", headers=auth(token))
    assert dashboard.status_code == 200, dashboard.text
    assert dashboard.json()["converted"] == 1
    reports = client.get("/api/v1/leads/analytics/reports", headers=auth(token))
    assert reports.status_code == 200, reports.text
    assert reports.json()["by_service"][0]["converted"] == 1


def test_accepted_proposal_generates_and_tracks_contract(client, token):
    lead = new_lead(client, token, cpf="11144477735")
    proposal = client.post(f"/api/v1/leads/{lead['id']}/proposals", headers=auth(token), json={"fixed_value": 1800, "installments": 3, "installment_value": 600, "status": "ACEITA"})
    assert proposal.status_code == 201, proposal.text
    converted = client.post(f"/api/v1/leads/{lead['id']}/convert", headers=auth(token), json={"create_recovery_case": False})
    assert converted.status_code == 200, converted.text

    templates = client.get("/api/v1/contracts/templates", headers=auth(token))
    assert templates.status_code == 200, templates.text
    template = templates.json()[0]
    created = client.post(f"/api/v1/leads/{lead['id']}/proposals/{proposal.json()['id']}/contract", headers=auth(token), json={"template_id": template["id"]})
    assert created.status_code == 201, created.text
    contract = created.json()
    assert contract["status"] == "RASCUNHO"
    assert contract["contract_number"].startswith("CTR-")
    assert "CONTRATO DE PRESTAÇÃO" in contract["content"]
    assert contract["template_id"] == template["id"]
    assert "Maria da Silva" in contract["content"]
    assert "{{cliente_nome}}" not in contract["content"]

    for target in ["EM_REVISAO", "APROVADO", "ENVIADO"]:
        changed = client.patch(f"/api/v1/leads/{lead['id']}/contracts/{contract['id']}/status", headers=auth(token), json={"status": target})
        assert changed.status_code == 200, changed.text
    signed = client.patch(f"/api/v1/leads/{lead['id']}/contracts/{contract['id']}/status", headers=auth(token), json={"status": "ASSINADO", "signature_reference": "Documento físico arquivado"})
    assert signed.status_code == 200, signed.text
    assert signed.json()["signed_at"]

    document = client.get(f"/api/v1/leads/{lead['id']}/contracts/{contract['id']}/document", headers=auth(token))
    assert document.status_code == 200
    assert "Imprimir / salvar em PDF" in document.text
    timeline = client.get(f"/api/v1/leads/{lead['id']}/timeline", headers=auth(token)).json()
    assert timeline["contracts"][0]["status"] == "ASSINADO"

    summary = client.get("/api/v1/contracts/summary", headers=auth(token))
    assert summary.status_code == 200, summary.text
    assert summary.json()["total"] == 1
    assert summary.json()["signed"] == 1
    listed = client.get("/api/v1/contracts?search=Maria&status=ASSINADO", headers=auth(token))
    assert listed.status_code == 200, listed.text
    assert listed.json()[0]["contract_number"] == contract["contract_number"]
    assert listed.json()[0]["client_name"] == "Maria da Silva"


def test_contract_template_crud(client, token):
    services = catalogs(client, token)["services"]
    service_id = next(item["id"] for item in services if item["code"] == "CS_RECUPERA")
    created = client.post("/api/v1/contracts/templates", headers=auth(token), json={
        "name": "Modelo CS Recupera", "title": "Contrato CS Recupera",
        "content": "CONTRATANTE: {{cliente_nome}}. SERVIÇO: {{servico}}. VALOR: {{valor_fixo}}.",
        "service_type_id": service_id, "active": True,
    })
    assert created.status_code == 201, created.text
    template_id = created.json()["id"]
    changed = client.patch(f"/api/v1/contracts/templates/{template_id}", headers=auth(token), json={"title": "Contrato CS Recupera atualizado"})
    assert changed.status_code == 200, changed.text
    assert changed.json()["title"].endswith("atualizado")
    deleted = client.delete(f"/api/v1/contracts/templates/{template_id}", headers=auth(token))
    assert deleted.status_code == 204, deleted.text
    listed = client.get("/api/v1/contracts/templates?active_only=false", headers=auth(token))
    assert all(item["id"] != template_id for item in listed.json())


def test_search_filters_and_soft_delete(client, token):
    lead = new_lead(client, token)
    found = client.get("/api/v1/leads?search=Maria&status=NOVO", headers=auth(token))
    assert found.status_code == 200 and len(found.json()) == 1
    deleted = client.delete(f"/api/v1/leads/{lead['id']}", headers=auth(token))
    assert deleted.status_code == 204
    assert client.get("/api/v1/leads?search=Maria", headers=auth(token)).json() == []


def test_converted_lead_can_create_recovery_case_later(client, token):
    lead = new_lead(client, token)
    converted = client.post(f"/api/v1/leads/{lead['id']}/convert", headers=auth(token), json={"create_recovery_case": False})
    assert converted.status_code == 200, converted.text
    assert converted.json()["recovery_case_id"] is None

    recovered = client.post(f"/api/v1/leads/{lead['id']}/convert", headers=auth(token), json={"create_recovery_case": True})
    assert recovered.status_code == 200, recovered.text
    assert recovered.json()["lead"]["status"] == "CONVERTIDO"
    assert recovered.json()["recovery_case_id"]
