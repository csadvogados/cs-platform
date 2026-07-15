def auth(token): return {'Authorization':f'Bearer {token}'}
def test_financial_diagnosis_flow(client,token):
    h=auth(token)
    c=client.post('/api/v1/clients',headers=h,json={'full_name':'Maria Teste','cpf':'52998224725','person_natural':True,'good_faith_declared':True,'can_pay_without_harming_basics':False})
    assert c.status_code==201,c.text; cid=c.json()['id']
    assert client.post(f'/api/v1/financial/clients/{cid}/incomes',headers=h,json={'income_type':'aposentadoria','net_amount':'4000'}).status_code==201
    assert client.post(f'/api/v1/financial/clients/{cid}/expenses',headers=h,json={'category':'moradia','amount':'2500'}).status_code==201
    assert client.post(f'/api/v1/financial/clients/{cid}/debts',headers=h,json={'nature':'personal_loan','current_balance':'20000','monthly_installment':'1800'}).status_code==201
    d=client.get(f'/api/v1/diagnoses/{cid}/preview',headers=h)
    assert d.status_code==200,d.text
    assert d.json()['eligibility_score']>=85
    r=client.get(f'/api/v1/diagnoses/{cid}/report',headers=h)
    assert r.status_code==200 and 'PARECER ECONÔMICO' in r.text
