def test_health(client):
    r = client.get("/api/v1/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"

def test_login_and_me(client, token):
    r = client.get("/api/v1/auth/me", headers={"Authorization":f"Bearer {token}"})
    assert r.status_code == 200
    assert r.json()["email"] == "admin@example.com"
