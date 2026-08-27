import calendar
from datetime import date
from decimal import Decimal, ROUND_HALF_UP

from app.services.diagnosis_engine import calculate

CENT = Decimal("0.01")
HUNDRED = Decimal("100")


def money(value) -> Decimal:
    return Decimal(value or 0).quantize(CENT, rounding=ROUND_HALF_UP)


def add_months(value: date, months: int) -> date:
    month_index = value.month - 1 + months
    year = value.year + month_index // 12
    month = month_index % 12 + 1
    day = min(value.day, calendar.monthrange(year, month)[1])
    return date(year, month, day)


def monthly_payment(principal: Decimal, annual_rate: Decimal, months: int) -> Decimal:
    if principal <= 0:
        return Decimal("0.00")
    monthly_rate = annual_rate / Decimal("1200")
    if monthly_rate == 0:
        return money(principal / months)
    factor = (Decimal("1") + monthly_rate) ** months
    return money(principal * monthly_rate * factor / (factor - Decimal("1")))


def simulate(client, payload, organization_id, minimum_existential: Decimal) -> dict:
    diagnosis = calculate(client, minimum_existential)
    selected_ids = set(payload.debt_ids or [])
    debts = [debt for debt in client.debts if not selected_ids or debt.id in selected_ids]
    found_ids = {debt.id for debt in debts}
    missing_ids = selected_ids - found_ids
    if missing_ids:
        raise ValueError("Uma ou mais dívidas selecionadas não pertencem ao cliente")

    total_debt = money(sum((money(debt.current_balance) for debt in debts), Decimal("0")))
    capacity = money(diagnosis["max_payment_capacity"])
    applied_limit = min(capacity, money(payload.maximum_installment)) if payload.maximum_installment else capacity
    start = payload.first_due_date or date.today()
    warnings: list[str] = []
    if not debts:
        warnings.append("Nenhuma dívida foi selecionada para a simulação.")
    if capacity <= 0:
        warnings.append("O diagnóstico não identificou capacidade mensal protegida para novo acordo.")
    if diagnosis["data_quality_score"] < 70:
        warnings.append("Complete os dados financeiros antes de aprovar um acordo definitivo.")

    scenarios = []
    rejected = 0
    for discount in sorted(set(payload.discount_percentages), reverse=True):
        negotiated = money(total_debt * (HUNDRED - discount) / HUNDRED)
        if payload.down_payment > negotiated:
            rejected += len(set(payload.installment_terms))
            continue
        financed = money(negotiated - payload.down_payment)
        for term in sorted(set(payload.installment_terms)):
            installment = monthly_payment(financed, payload.annual_interest_rate, term)
            total_payable = money(payload.down_payment + installment * term)
            total_interest = money(max(Decimal("0"), total_payable - negotiated))
            sustainable = applied_limit > 0 and installment <= applied_limit and installment >= payload.minimum_installment
            scenario_warnings = []
            if installment > applied_limit:
                scenario_warnings.append("Parcela acima da capacidade mensal protegida.")
            if installment < payload.minimum_installment:
                scenario_warnings.append("Parcela abaixo do mínimo operacional informado.")
            capacity_usage = Decimal("0") if applied_limit <= 0 else money(installment / applied_limit * HUNDRED)
            score = 100
            if not sustainable:
                score -= 55
            score -= min(25, max(0, int(capacity_usage - Decimal("70"))))
            score -= min(15, term // 12)
            score += min(15, int(discount / Decimal("2")))
            score = max(0, min(100, score))
            scenarios.append({
                "term_months": term,
                "discount_percentage": money(discount),
                "annual_interest_rate": money(payload.annual_interest_rate),
                "original_amount": total_debt,
                "negotiated_amount": negotiated,
                "down_payment": money(payload.down_payment),
                "financed_amount": financed,
                "installment_amount": installment,
                "total_payable": total_payable,
                "total_interest": total_interest,
                "first_due_date": start,
                "last_due_date": add_months(start, term - 1),
                "capacity_usage_percentage": capacity_usage,
                "sustainable": sustainable,
                "score": score,
                "recommendation": "Cenário recomendado para negociação" if sustainable and score >= 80 else "Viável com atenção" if sustainable else "Não recomendado",
                "warnings": scenario_warnings,
            })

    scenarios.sort(key=lambda item: (not item["sustainable"], -item["score"], item["total_payable"], item["term_months"]))
    for rank, scenario in enumerate(scenarios, start=1):
        scenario["rank"] = rank
    return {
        "client_id": client.id,
        "organization_id": organization_id,
        "selected_debt_ids": [debt.id for debt in debts],
        "total_debt_amount": total_debt,
        "calculated_payment_capacity": capacity,
        "applied_payment_limit": applied_limit,
        "minimum_existential_reference": money(minimum_existential),
        "data_quality_score": diagnosis["data_quality_score"],
        "scenarios": scenarios,
        "rejected_scenarios": rejected,
        "warnings": warnings,
    }
