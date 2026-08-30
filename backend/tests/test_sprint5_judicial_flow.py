def auth(token):
    return {"Authorization": f"Bearer {token}"}


def test_case_stage_progression_and_judicial_gate(client, token):
    headers = auth(token)
    customer = client.post("/api/v1/clients", headers=headers, json={
        "full_name": "Cliente Judicial", "cpf": "52998224725",
        "good_faith_declared": True, "can_pay_without_harming_basics": False,
    }).json()
    case = client.post("/api/v1/recovery-cases", headers=headers, json={"client_id": customer["id"]}).json()
    case = client.post(f"/api/v1/recovery-cases/{case['id']}/transitions", headers=headers, json={"status": "active", "version": case["version"]}).json()
    for stage in ("documents", "diagnosis", "planning", "negotiation", "judicial_preparation"):
        response = client.patch(f"/api/v1/recovery-cases/{case['id']}", headers=headers, json={"stage": stage, "version": case["version"]})
        assert response.status_code == 200, response.text
        case = response.json()

    blocked = client.post(f"/api/v1/recovery-cases/{case['id']}/transitions", headers=headers, json={"status": "judicialized", "version": case["version"]})
    assert blocked.status_code == 422
    assert "documentos obrigatórios" in blocked.json()["error"]["message"]

    client.post(f"/api/v1/financial/clients/{customer['id']}/incomes", headers=headers, json={"income_type": "salary", "net_amount": "4000"})
    client.post(f"/api/v1/financial/clients/{customer['id']}/expenses", headers=headers, json={"category": "housing", "amount": "2000"})
    client.post(f"/api/v1/financial/clients/{customer['id']}/debts", headers=headers, json={"nature": "consumer", "current_balance": "8000", "monthly_installment": "500"})
    assert client.post(f"/api/v1/diagnoses/{customer['id']}", headers=headers).status_code == 201
    for category in ("identification", "income_proof", "residence_proof", "debt_statement"):
        uploaded = client.post(f"/api/v1/documents/clients/{customer['id']}", headers=headers, data={"category": category}, files={"file": (f"{category}.pdf", b"%PDF-1.4", "application/pdf")})
        assert uploaded.status_code == 201, uploaded.text
        assert client.post(f"/api/v1/documents/{uploaded.json()['id']}/validation", headers=headers, json={"status": "validated"}).status_code == 200

    judicialized = client.post(f"/api/v1/recovery-cases/{case['id']}/transitions", headers=headers, json={"status": "judicialized", "version": case["version"]})
    assert judicialized.status_code == 200, judicialized.text
    assert judicialized.json()["status"] == "judicialized"
    assert judicialized.json()["stage"] == "closed"


def test_case_cannot_skip_internal_stage(client, token):
    headers = auth(token)
    customer = client.post("/api/v1/clients", headers=headers, json={"full_name": "Cliente Etapa", "cpf": "11144477735"}).json()
    case = client.post("/api/v1/recovery-cases", headers=headers, json={"client_id": customer["id"]}).json()
    case = client.post(f"/api/v1/recovery-cases/{case['id']}/transitions", headers=headers, json={"status": "active", "version": case["version"]}).json()
    skipped = client.patch(f"/api/v1/recovery-cases/{case['id']}", headers=headers, json={"stage": "judicial_preparation", "version": case["version"]})
    assert skipped.status_code == 409
