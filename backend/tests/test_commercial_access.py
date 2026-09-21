"""Regression coverage for the manually validated commercial permission matrix."""
from types import SimpleNamespace
from uuid import uuid4

from app.api.deps import get_identity_context
from app.main import app


def test_commercial_roles_and_profile_organization_scope(client, token):
    headers = {"Authorization": f"Bearer {token}"}
    me = client.get("/api/v1/auth/me", headers=headers).json()
    from uuid import UUID
    identity = SimpleNamespace(
        user_id=UUID(me["id"]), organization_id=UUID(me["organization_id"]),
        role="admin", is_superuser=False,
    )
    app.dependency_overrides[get_identity_context] = lambda: identity
    try:
        for index, (role, expected) in enumerate([("admin", 201), ("advogado", 201), ("atendimento", 201), ("financeiro", 403)]):
            identity.role = role
            response = client.post("/api/v1/clients", headers=headers, json={"full_name": f"Teste {role}", "cpf": f"1234567890{index}"})
            assert response.status_code == expected, response.text
            if role == "admin":
                client_id = response.json()["id"]

        for role in ["admin", "advogado", "atendimento", "financeiro", "negociador"]:
            identity.role = role
            assert client.get(f"/api/v1/clients/{client_id}/profile", headers=headers).status_code == 200

        identity.role = "cliente"
        assert client.get(f"/api/v1/clients/{client_id}/profile", headers=headers).status_code == 403
        assert client.get("/api/v1/leads", headers=headers).status_code == 403

        identity.role = "atendimento"
        assert client.delete(f"/api/v1/leads/{uuid4()}", headers=headers).status_code == 403
        identity.role = "negociador"
        assert client.post(f"/api/v1/leads/{uuid4()}/convert", headers=headers, json={}).status_code == 403

        identity.role = "admin"
        identity.organization_id = uuid4()
        assert client.get(f"/api/v1/clients/{client_id}/profile", headers=headers).status_code == 404
        assert client.get(f"/api/v1/clients/{client_id}", headers=headers).status_code == 404
    finally:
        app.dependency_overrides.pop(get_identity_context, None)
