def auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def test_consolidated_dossier_flow(client, token):
    headers = auth(token)
    created = client.post(
        "/api/v1/clients",
        headers=headers,
        json={
            "full_name": "Cliente Dossiê",
            "cpf": "52998224725",
            "person_natural": True,
            "good_faith_declared": True,
            "can_pay_without_harming_basics": False,
        },
    )
    assert created.status_code == 201, created.text
    client_id = created.json()["id"]

    income = client.post(
        f"/api/v1/financial/clients/{client_id}/incomes",
        headers=headers,
        json={"income_type": "salário", "net_amount": "4200.00"},
    )
    expense = client.post(
        f"/api/v1/financial/clients/{client_id}/expenses",
        headers=headers,
        json={"category": "moradia", "amount": "2500.00"},
    )
    creditor = client.post(
        "/api/v1/financial/creditors",
        headers=headers,
        json={"legal_name": "Banco do Teste", "consumer_gov_enabled": True},
    )
    assert income.status_code == expense.status_code == creditor.status_code == 201
    debt = client.post(
        f"/api/v1/financial/clients/{client_id}/debts",
        headers=headers,
        json={
            "creditor_id": creditor.json()["id"],
            "nature": "personal_loan",
            "current_balance": "18000.00",
            "monthly_installment": "1600.00",
            "overdue": True,
        },
    )
    assert debt.status_code == 201, debt.text
    saved = client.post(f"/api/v1/diagnoses/{client_id}", headers=headers)
    assert saved.status_code == 201, saved.text

    response = client.get(f"/api/v1/diagnoses/{client_id}/dossier", headers=headers)
    assert response.status_code == 200, response.text
    dossier = response.json()
    assert dossier["client"]["id"] == client_id
    assert dossier["creditors"][0]["legal_name"] == "Banco do Teste"
    assert dossier["debts"][0]["creditor_name"] == "Banco do Teste"
    assert dossier["latest_diagnosis"]["version"] == 1
    assert dossier["financial_summary"]["total_debt_balance"] == "18000.00"
    assert dossier["missing_information"] == []


def test_archived_client_dossier_is_not_accessible(client, token):
    headers = auth(token)
    created = client.post(
        "/api/v1/clients",
        headers=headers,
        json={"full_name": "Cliente Arquivado", "cpf": "11144477735"},
    )
    assert created.status_code == 201
    client_id = created.json()["id"]
    assert client.delete(f"/api/v1/clients/{client_id}", headers=headers).status_code == 204
    assert client.get(
        f"/api/v1/diagnoses/{client_id}/dossier", headers=headers
    ).status_code == 404
