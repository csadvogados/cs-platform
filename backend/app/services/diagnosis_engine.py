from decimal import ROUND_HALF_UP, Decimal
from unicodedata import combining, normalize

ELIGIBLE = {
    "consumer",
    "credit_card",
    "overdraft",
    "personal_loan",
    "payroll_loan",
    "essential_service",
}

ATTENTION = {
    "secured_debt",
    "real_estate_financing",
    "rural_credit",
    "luxury_high_value",
    "tax",
    "alimony",
    "rent_condo",
}

NATURE_ALIASES = {
    "cartao de credito": "credit_card",
    "cheque especial": "overdraft",
    "emprestimo pessoal": "personal_loan",
    "emprestimo consignado": "payroll_loan",
    "servico essencial": "essential_service",
    "divida de consumo": "consumer",
    "outra": "consumer",
    "outra divida de consumo": "consumer",
    "divida com garantia": "secured_debt",
    "financiamento": "real_estate_financing",
    "financiamento imobiliario": "real_estate_financing",
    "credito rural": "rural_credit",
    "divida tributaria": "tax",
    "pensao alimenticia": "alimony",
    "aluguel ou condominio": "rent_condo",
}


def money(value):
    return Decimal(value or 0).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def normalized_nature(value: str | None) -> str:
    raw = str(value or "").strip().casefold()
    if raw in ELIGIBLE or raw in ATTENTION:
        return raw
    folded = "".join(
        character
        for character in normalize("NFKD", raw)
        if not combining(character)
    )
    return NATURE_ALIASES.get(folded, folded)


def calculate(client, minimum=Decimal("600.00")):
    income = sum(
        (money(item.net_amount) for item in client.incomes if item.recurring),
        Decimal("0"),
    )
    expenses = sum(
        (
            money(item.amount)
            for item in client.expenses
            if item.recurring and item.essential
        ),
        Decimal("0"),
    )
    debt = sum(
        (money(item.current_balance) for item in client.debts),
        Decimal("0"),
    )
    installments = sum(
        (money(item.monthly_installment) for item in client.debts),
        Decimal("0"),
    )
    disposable = income - expenses - installments
    commitment = (
        Decimal("0")
        if income == 0
        else (installments / income * 100).quantize(Decimal("0.01"))
    )

    debt_natures = [normalized_nature(item.nature) for item in client.debts]
    eligible = sum(1 for nature in debt_natures if nature in ELIGIBLE)
    attention = sum(1 for nature in debt_natures if nature in ATTENTION)

    score = 0
    breakdown = {"person_profile": 0, "good_faith": 0, "payment_distress": 0, "eligible_debts": 0, "minimum_existential": 0}
    alerts = []
    if client.person_natural:
        score += 20
        breakdown["person_profile"] = 20
    else:
        alerts.append("O regime é direcionado à pessoa natural.")

    if client.good_faith_declared is True:
        score += 20
        breakdown["good_faith"] = 20
    elif client.good_faith_declared is None:
        score += 8
        breakdown["good_faith"] = 8
        alerts.append("A boa-fé deve ser apurada documentalmente.")
    else:
        alerts.append("Há indicação contrária à boa-fé.")

    if client.can_pay_without_harming_basics is False:
        score += 20
        breakdown["payment_distress"] = 20
    elif client.can_pay_without_harming_basics is None:
        score += 10
        breakdown["payment_distress"] = 10
        alerts.append("A capacidade de pagamento ainda não foi confirmada.")

    if eligible:
        score += 20
        breakdown["eligible_debts"] = 20
    else:
        alerts.append("Não há dívida de consumo potencialmente elegível cadastrada.")

    if disposable < minimum:
        score += 20
        breakdown["minimum_existential"] = 20
    elif income and disposable < income * Decimal("0.25"):
        score += 10
        breakdown["minimum_existential"] = 10

    if attention:
        alerts.append(f"{attention} dívida(s) exige(m) tratamento específico.")
    if income == 0:
        alerts.append("Renda recorrente não cadastrada.")

    result = (
        "Forte indicação para o programa"
        if score >= 85
        else (
            "Requer análise jurídica complementar"
            if score >= 60
            else "Baixa aderência preliminar"
        )
    )
    conclusion = (
        f"Renda: R$ {income:.2f}; despesas essenciais: R$ {expenses:.2f}; "
        f"parcelas: R$ {installments:.2f}; comprometimento: {commitment:.2f}%; "
        f"saldo estimado: R$ {disposable:.2f}. Resultado: {result} ({score}/100)."
    )
    data_checks = [income > 0, expenses > 0, debt > 0, bool(debt_natures), client.good_faith_declared is not None, client.can_pay_without_harming_basics is not None]
    data_quality_score = round(sum(data_checks) / len(data_checks) * 100)
    max_payment_capacity = max(Decimal("0"), income - expenses - minimum).quantize(Decimal("0.01"))
    risk_level = "critical" if commitment >= 80 or disposable < 0 else "high" if commitment >= 50 or disposable < minimum else "moderate" if debt else "low"
    recommended_strategy = "judicial_assessment" if attention and not eligible else "protected_negotiation" if score >= 85 else "document_review" if score >= 60 else "financial_orientation"
    return {
        "total_income": income,
        "total_expenses": expenses,
        "total_debt_balance": debt,
        "total_installments": installments,
        "disposable_income": disposable,
        "commitment_percentage": commitment,
        "minimum_existential_reference": minimum,
        "eligibility_score": score,
        "eligibility_result": result,
        "economic_conclusion": conclusion,
        "legal_alerts": alerts,
        "eligible_debts": eligible,
        "attention_debts": attention,
        "chart_data": {
            "income": float(income),
            "expenses": float(expenses),
            "installments": float(installments),
            "balance": float(max(disposable, Decimal("0"))),
        },
        "risk_level": risk_level,
        "recommended_strategy": recommended_strategy,
        "max_payment_capacity": max_payment_capacity,
        "data_quality_score": data_quality_score,
        "score_breakdown": breakdown,
        "analysis_snapshot": {"eligible_debts": eligible, "attention_debts": attention, "debt_natures": debt_natures},
    }
