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
