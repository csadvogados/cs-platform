def auth(client):
    r=client.post("/api/v1/auth/token",data={"username":"admin@example.com","password":"StrongPass123!"})
    assert r.status_code==200,r.text
    return {"Authorization":f"Bearer {r.json()['access_token']}"}

def test_seed_roles_permissions(client):
    h=auth(client)
    roles=client.get("/api/v1/roles",headers=h); perms=client.get("/api/v1/permissions",headers=h)
    assert roles.status_code==200,roles.text; assert perms.status_code==200,perms.text
    assert any(x["slug"]=="admin" for x in roles.json()); assert len(perms.json())>=20

def test_user_crud_pagination_and_block(client):
    h=auth(client)
    r=client.post("/api/v1/users",headers=h,json={"full_name":"Maria Silva","email":"maria@example.com","password":"VeryStrong123!","role":"advogado"})
    assert r.status_code==201,r.text; uid=r.json()["id"]
    page=client.get("/api/v1/users?page=1&page_size=10&q=Maria",headers=h)
    assert page.status_code==200,page.text; assert page.json()["total"]==1
    blocked=client.post(f"/api/v1/users/{uid}/block",headers=h); assert blocked.status_code==200; assert blocked.json()["status"]=="inactive"
    deleted=client.delete(f"/api/v1/users/{uid}",headers=h); assert deleted.status_code==204

def test_invitation_accept(client):
    h=auth(client)
    r=client.post("/api/v1/invitations",headers=h,json={"full_name":"João Convite","email":"joao@example.com","expires_in_hours":24})
    assert r.status_code==201,r.text
    accepted=client.post("/api/v1/invitations/accept",json={"token":r.json()["token"],"password":"InviteStrong123!"})
    assert accepted.status_code==201,accepted.text

def test_admin_resets_temporary_password_revokes_sessions_and_audits(client):
    h=auth(client)
    created=client.post("/api/v1/users",headers=h,json={"full_name":"Financeiro Teste","email":"financeiro@example.com","password":"OldStrongPass123!","role":"financeiro"})
    assert created.status_code==201,created.text
    uid=created.json()["id"]
    login=client.post("/api/v1/auth/login",json={"email":"financeiro@example.com","password":"OldStrongPass123!"})
    assert login.status_code==200,login.text
    old_refresh=login.json()["refresh_token"]

    reset=client.post(f"/api/v1/users/{uid}/reset-password",headers=h,json={"new_password":"TemporaryPass456!"})
    assert reset.status_code==204,reset.text
    assert client.post("/api/v1/auth/login",json={"email":"financeiro@example.com","password":"OldStrongPass123!"}).status_code==401
    new_login=client.post("/api/v1/auth/login",json={"email":"financeiro@example.com","password":"TemporaryPass456!"})
    assert new_login.status_code==200,new_login.text
    assert new_login.json()["must_change_password"] is True
    assert client.post("/api/v1/auth/refresh",json={"refresh_token":old_refresh}).status_code==401

    audit=client.get("/api/v1/audit?action=reset_password",headers=h)
    assert audit.status_code==200,audit.text
    event=next(item for item in audit.json()["items"] if item["entity_id"]==uid)
    assert event["details"]=={"sessions_revoked":True,"force_change_next_login":True}

def test_non_admin_cannot_reset_password(client):
    h=auth(client)
    created=client.post("/api/v1/users",headers=h,json={"full_name":"Atendimento Teste","email":"atendimento-reset@example.com","password":"SupportPass123!","role":"atendimento"})
    assert created.status_code==201,created.text
    login=client.post("/api/v1/auth/login",json={"email":"atendimento-reset@example.com","password":"SupportPass123!"})
    support_headers={"Authorization":f"Bearer {login.json()['access_token']}"}
    response=client.post(f"/api/v1/users/{created.json()['id']}/reset-password",headers=support_headers,json={"new_password":"AnotherPass456!"})
    assert response.status_code==403,response.text
