from decimal import Decimal, ROUND_HALF_UP
ELIGIBLE = {'consumer','credit_card','overdraft','personal_loan','payroll_loan','essential_service'}
ATTENTION = {'secured_debt','real_estate_financing','rural_credit','luxury_high_value','tax','alimony','rent_condo'}
def money(v): return Decimal(v or 0).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
def calculate(client, minimum=Decimal('600.00')):
    income=sum((money(x.net_amount) for x in client.incomes if x.recurring),Decimal('0'))
    expenses=sum((money(x.amount) for x in client.expenses if x.recurring and x.essential),Decimal('0'))
    debt=sum((money(x.current_balance) for x in client.debts),Decimal('0'))
    installments=sum((money(x.monthly_installment) for x in client.debts),Decimal('0'))
    disposable=income-expenses-installments
    commitment=Decimal('0') if income==0 else (installments/income*100).quantize(Decimal('0.01'))
    eligible=sum(1 for x in client.debts if x.nature in ELIGIBLE); attention=sum(1 for x in client.debts if x.nature in ATTENTION)
    score=0; alerts=[]
    if client.person_natural: score+=20
    else: alerts.append('O regime é direcionado à pessoa natural.')
    if client.good_faith_declared is True: score+=20
    elif client.good_faith_declared is None: score+=8; alerts.append('A boa-fé deve ser apurada documentalmente.')
    else: alerts.append('Há indicação contrária à boa-fé.')
    if client.can_pay_without_harming_basics is False: score+=20
    elif client.can_pay_without_harming_basics is None: score+=10; alerts.append('A capacidade de pagamento ainda não foi confirmada.')
    if eligible: score+=20
    else: alerts.append('Não há dívida de consumo potencialmente elegível cadastrada.')
    if disposable<minimum: score+=20
    elif income and disposable<income*Decimal('0.25'): score+=10
    if attention: alerts.append(f'{attention} dívida(s) exige(m) tratamento específico.')
    if income==0: alerts.append('Renda recorrente não cadastrada.')
    result='Forte indicação para o programa' if score>=85 else ('Requer análise jurídica complementar' if score>=60 else 'Baixa aderência preliminar')
    conclusion=f'Renda: R$ {income:.2f}; despesas essenciais: R$ {expenses:.2f}; parcelas: R$ {installments:.2f}; comprometimento: {commitment:.2f}%; saldo estimado: R$ {disposable:.2f}. Resultado: {result} ({score}/100).'
    return {'total_income':income,'total_expenses':expenses,'total_debt_balance':debt,'total_installments':installments,'disposable_income':disposable,'commitment_percentage':commitment,'minimum_existential_reference':minimum,'eligibility_score':score,'eligibility_result':result,'economic_conclusion':conclusion,'legal_alerts':alerts,'eligible_debts':eligible,'attention_debts':attention,'chart_data':{'income':float(income),'expenses':float(expenses),'installments':float(installments),'balance':float(max(disposable,Decimal('0')))}}
