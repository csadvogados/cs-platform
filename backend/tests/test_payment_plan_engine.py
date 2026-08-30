from decimal import Decimal


def auth(token):
    return {"Authorization": f"Bearer {token}"}


def create_financial_profile(client, token):
    headers = auth(token)
    created = client.post(
        "/api/v1/clients",
        headers=headers,
        json={"full_name": "Cliente Plano", "cpf": "39053344705"},
    )
    assert created.status_code == 201, created.text
    client_id = created.json()["id"]
    assert client.post(
        f"/api/v1/financial/clients/{client_id}/incomes",
        headers=headers,
        json={"income_type": "salary", "net_amount": "5000"},
    ).status_code == 201
    assert client.post(
        f"/api/v1/financial/clients/{client_id}/expenses",
        headers=headers,
        json={"category": "housing", "amount": "2500"},
    ).status_code == 201
    debt = client.post(
        f"/api/v1/financial/clients/{client_id}/debts",
        headers=headers,
        json={"nature": "credit_card", "current_balance": "12000", "monthly_installment": "0"},
    )
    assert debt.status_code == 201, debt.text
    return client_id, debt.json()["id"]


def test_simulation_ranks_sustainable_scenarios(client, token):
    client_id, debt_id = create_financial_profile(client, token)
    response = client.post(
        f"/api/v1/payment-plans/{client_id}/simulate",
        headers=auth(token),
        json={
            "debt_ids": [debt_id],
            "discount_percentages": [0, 20],
            "installment_terms": [6, 12, 24],
            "annual_interest_rate": "0",
            "down_payment": "0",
        },
    )
    assert response.status_code == 200, response.text
    result = response.json()
    assert result["total_debt_amount"] == "12000.00"
    assert result["calculated_payment_capacity"] == "1900.00"
    assert len(result["scenarios"]) == 6
    assert result["scenarios"][0]["sustainable"] is True
    assert result["scenarios"][0]["rank"] == 1
    assert Decimal(result["scenarios"][0]["installment_amount"]) <= Decimal(result["applied_payment_limit"])


def test_simulation_rejects_debt_from_another_client(client, token):
    first_client_id, _ = create_financial_profile(client, token)
    other = client.post(
        "/api/v1/clients",
        headers=auth(token),
        json={"full_name": "Outro Cliente", "cpf": "52998224725"},
    )
    other_id = other.json()["id"]
    foreign_debt = client.post(
        f"/api/v1/financial/clients/{other_id}/debts",
        headers=auth(token),
        json={"nature": "consumer", "current_balance": "1000", "monthly_installment": "0"},
    ).json()["id"]
    response = client.post(
        f"/api/v1/payment-plans/{first_client_id}/simulate",
        headers=auth(token),
        json={"debt_ids": [foreign_debt]},
    )
    assert response.status_code == 422


def test_simulation_rejects_archived_client(client, token):
    client_id, _ = create_financial_profile(client, token)
    assert client.delete(
        f"/api/v1/clients/{client_id}", headers=auth(token)
    ).status_code == 204
    response = client.post(
        f"/api/v1/payment-plans/{client_id}/simulate",
        headers=auth(token),
        json={},
    )
    assert response.status_code == 404
