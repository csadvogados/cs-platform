from datetime import date, timedelta


def auth(token):
    return {"Authorization": f"Bearer {token}"}


def setup_case(client, token):
    headers = auth(token)
    customer = client.post("/api/v1/clients", headers=headers, json={"full_name": "Cliente Negociação", "cpf": "11144477735"})
    assert customer.status_code == 201, customer.text
    client_id = customer.json()["id"]
    client.post(f"/api/v1/financial/clients/{client_id}/incomes", headers=headers, json={"income_type": "salary", "net_amount": "5000"})
    client.post(f"/api/v1/financial/clients/{client_id}/expenses", headers=headers, json={"category": "housing", "amount": "2500"})
    debt = client.post(f"/api/v1/financial/clients/{client_id}/debts", headers=headers,
                       json={"nature": "credit_card", "current_balance": "12000", "monthly_installment": "0"})
    assert debt.status_code == 201, debt.text
    case = client.post("/api/v1/recovery-cases", headers=headers, json={"client_id": client_id})
    assert case.status_code == 201, case.text
    return client_id, debt.json()["id"], case.json()["id"]


def test_negotiation_offer_is_evaluated_and_accepted(client, token):
    client_id, debt_id, case_id = setup_case(client, token)
    negotiation = client.post("/api/v1/negotiations", headers=auth(token), json={
        "recovery_case_id": case_id, "debt_id": debt_id, "channel": "whatsapp"
    })
    assert negotiation.status_code == 201, negotiation.text
    negotiation_id = negotiation.json()["id"]
    offer = client.post(f"/api/v1/negotiations/{negotiation_id}/offers", headers=auth(token), json={
        "origin": "creditor", "offered_amount": "9600", "down_payment": "0",
        "installment_count": 12, "installment_amount": "800", "annual_interest_rate": "0",
        "first_due_date": str(date.today() + timedelta(days=30)),
    })
    assert offer.status_code == 201, offer.text
    result = offer.json()
    assert result["sustainable"] is True
    assert result["engine_decision"] == "accept"
    decided = client.post(
        f"/api/v1/negotiations/{negotiation_id}/offers/{result['id']}/decision",
        headers=auth(token), json={"status": "accepted", "reason": "Aprovada pelo cliente"},
    )
    assert decided.status_code == 200, decided.text
    assert decided.json()["status"] == "accepted"
    assert decided.json()["offers"][0]["status"] == "accepted"


def test_negotiation_rejects_debt_from_another_client(client, token):
    _, _, case_id = setup_case(client, token)
    other = client.post("/api/v1/clients", headers=auth(token), json={"full_name": "Outro", "cpf": "52998224725"})
    other_debt = client.post(f"/api/v1/financial/clients/{other.json()['id']}/debts", headers=auth(token),
                             json={"nature": "consumer", "current_balance": "1000", "monthly_installment": "0"})
    response = client.post("/api/v1/negotiations", headers=auth(token), json={
        "recovery_case_id": case_id, "debt_id": other_debt.json()["id"], "channel": "email"
    })
    assert response.status_code == 422
