from datetime import datetime, timezone

def create_client(client,token):
 r=client.post('/api/v1/clients',headers={'Authorization':f'Bearer {token}'},json={'full_name':'Cliente CRM','cpf':'12345678901','email':'crm@example.com'})
 assert r.status_code==201,r.text
 return r.json()['id']

def test_crm_flow(client,token):
 h={'Authorization':f'Bearer {token}'}; cid=create_client(client,token)
 r=client.post('/api/v1/crm/contacts',headers=h,json={'client_id':cid,'name':'Contato Principal','email':'contato@example.com'});assert r.status_code==201,r.text
 r=client.post('/api/v1/crm/interactions',headers=h,json={'client_id':cid,'interaction_type':'call','subject':'Contato inicial','occurred_at':datetime.now(timezone.utc).isoformat()});assert r.status_code==201,r.text
 r=client.post('/api/v1/crm/opportunities',headers=h,json={'client_id':cid,'title':'Contrato consultivo','estimated_value':15000,'probability':60});assert r.status_code==201,r.text; oid=r.json()['id']
 r=client.post('/api/v1/crm/tasks',headers=h,json={'client_id':cid,'opportunity_id':oid,'title':'Enviar proposta'});assert r.status_code==201,r.text;tid=r.json()['id']
 assert client.post(f'/api/v1/crm/tasks/{tid}/complete',headers=h).status_code==200
 s=client.get('/api/v1/crm/summary',headers=h);assert s.status_code==200;assert s.json()['opportunities']==1;assert s.json()['open_pipeline_value']==15000

def test_crm_requires_auth(client):
 assert client.get('/api/v1/crm/summary').status_code==401
