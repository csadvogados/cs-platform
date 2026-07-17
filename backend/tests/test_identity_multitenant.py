from app.core.security import create_access_token


def test_me_returns_identity_context(client, token):
    response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200, response.text
    payload = response.json()
    assert payload["email"] == "admin@example.com"
    assert payload["organization_id"] == payload["organization"]["id"]
    assert payload["is_superuser"] is True
    assert "organization.update" in payload["permissions"]


def test_rejects_token_with_wrong_organization_claim(client, token):
    current = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    ).json()
    forged = create_access_token(
        current["id"],
        {"org": "00000000-0000-0000-0000-000000000001", "role": current["role"]},
    )
    response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {forged}"},
    )
    assert response.status_code == 401


def test_rejects_token_with_stale_role_claim(client, token):
    current = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    ).json()
    forged = create_access_token(
        current["id"],
        {"org": current["organization_id"], "role": "atendimento"},
    )
    response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {forged}"},
    )
    assert response.status_code == 401
