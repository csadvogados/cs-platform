from app.core.security import create_access_token


def auth(token):
    return {"Authorization": f"Bearer {token}"}


def test_judicial_dossier_consolidates_case_and_renders_report(client, token):
    headers = auth(token)
    customer = client.post("/api/v1/clients", headers=headers, json={
        "full_name": "Cliente Dossiê Judicial", "cpf": "52998224725",
        "good_faith_declared": True, "can_pay_without_harming_basics": True,
    }).json()
    client.post(f"/api/v1/financial/clients/{customer['id']}/incomes", headers=headers,
                json={"income_type": "salario", "net_amount": 5000, "recurring": True})
    client.post(f"/api/v1/financial/clients/{customer['id']}/expenses", headers=headers,
                json={"category": "moradia", "amount": 2200, "essential": True, "recurring": True})
    creditor = client.post("/api/v1/financial/creditors", headers=headers,
                           json={"legal_name": "Banco Dossiê"}).json()
    client.post(f"/api/v1/financial/clients/{customer['id']}/debts", headers=headers, json={
        "creditor_id": creditor["id"], "nature": "consumer_credit",
        "current_balance": 18000, "monthly_installment": 900, "overdue": True,
    })
    recovery = client.post("/api/v1/recovery-cases", headers=headers,
                           json={"client_id": customer["id"]})
    assert recovery.status_code == 201, recovery.text

    response = client.get(f"/api/v1/diagnoses/{customer['id']}/judicial-dossier", headers=headers)
    assert response.status_code == 200, response.text
    dossier = response.json()
    assert dossier["client"]["name"] == "Cliente Dossiê Judicial"
    assert dossier["financial"]["total_debt_balance"] == 18000.0
    assert dossier["debts"][0]["creditor"] == "Banco Dossiê"
    assert dossier["cases"][0]["number"].startswith("REC-")
    assert dossier["timeline"][0]["type"] == "case_opened"
    assert dossier["checklist"]["ready"] is False

    report = client.get(f"/api/v1/diagnoses/{customer['id']}/judicial-dossier/report", headers=headers)
    assert report.status_code == 200, report.text
    assert "DOSSIÊ DE JUDICIALIZAÇÃO" in report.text
    assert "Banco Dossiê" in report.text
    audit = client.get("/api/v1/audit?entity_type=judicial_dossier&action=export", headers=headers).json()
    assert audit["total"] == 1


def test_support_cannot_access_judicial_dossier(client, token):
    headers = auth(token)
    customer = client.post("/api/v1/clients", headers=headers,
                           json={"full_name": "Cliente Restrito", "cpf": "11144477735"}).json()
    user = client.post("/api/v1/users", headers=headers, json={
        "full_name": "Atendimento Restrito", "email": "dossie-atendimento@example.com",
        "password": "SenhaMuitoForte123!", "role": "atendimento",
    }).json()
    support_headers = auth(create_access_token(user["id"]))
    assert client.get(f"/api/v1/diagnoses/{customer['id']}/judicial-dossier", headers=support_headers).status_code == 403
    assert client.get(f"/api/v1/diagnoses/{customer['id']}/judicial-dossier/report", headers=support_headers).status_code == 403
