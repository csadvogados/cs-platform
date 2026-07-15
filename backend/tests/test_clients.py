def test_create_list_update_client(client, token):
    headers={"Authorization":f"Bearer {token}"}
    payload={"full_name":"Maria da Silva","cpf":"12345678901","phone":"13999990000","city":"Peruíbe","state":"sp","person_natural":True,"good_faith_declared":True}
    created=client.post("/api/v1/clients",json=payload,headers=headers)
    assert created.status_code == 201, created.text
    cid=created.json()["id"]
    assert created.json()["state"] == "SP"
    listed=client.get("/api/v1/clients?q=Maria",headers=headers)
    assert listed.status_code == 200 and len(listed.json()) == 1
    updated=client.patch(f"/api/v1/clients/{cid}",json={"status":"contracted"},headers=headers)
    assert updated.status_code == 200
    assert updated.json()["status"] == "contracted"

def test_duplicate_cpf(client, token):
    headers={"Authorization":f"Bearer {token}"}
    payload={"full_name":"Cliente Um","cpf":"98765432100"}
    assert client.post("/api/v1/clients",json=payload,headers=headers).status_code == 201
    payload["full_name"]="Cliente Dois"
    assert client.post("/api/v1/clients",json=payload,headers=headers).status_code == 409
