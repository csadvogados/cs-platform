from decimal import Decimal, ROUND_HALF_UP

CENT = Decimal("0.01")


def money(value) -> Decimal:
    return Decimal(value or 0).quantize(CENT, rounding=ROUND_HALF_UP)


def evaluate_offer(*, debt_amount, offered_amount, installment_amount, down_payment, payment_capacity, data_quality_score):
    original = money(debt_amount)
    offered = money(offered_amount)
    installment = money(installment_amount)
    capacity = money(payment_capacity)
    discount = Decimal("0") if original <= 0 else (original - offered) / original * 100
    usage = Decimal("0") if capacity <= 0 else installment / capacity * 100
    sustainable = capacity > 0 and installment <= capacity
    score = 50
    score += min(25, max(0, int(discount)))
    score += 20 if sustainable else -40
    score -= max(0, min(20, int(usage - Decimal("80"))))
    score += 5 if down_payment <= payment_capacity else -10
    if data_quality_score < 70:
        score -= 15
    score = max(0, min(100, score))

    if data_quality_score < 50:
        decision = "manual_review"
        reason = "Dados financeiros insuficientes para decisão automática segura."
    elif sustainable and score >= 75:
        decision = "accept"
        reason = "A proposta respeita a capacidade protegida e apresenta condições favoráveis."
    elif sustainable:
        decision = "counter"
        reason = "A proposta cabe no orçamento, mas pode ser melhorada em desconto ou prazo."
    else:
        decision = "reject"
        reason = "A parcela supera a capacidade mensal protegida do cliente."
    return {
        "sustainable": sustainable,
        "capacity_usage_percentage": money(usage),
        "engine_score": score,
        "engine_decision": decision,
        "engine_reason": reason,
    }
