import calendar
from datetime import date
from decimal import Decimal, ROUND_HALF_UP

from app.models.financial import PaymentAgreement, PaymentInstallment

CENT = Decimal("0.01")


def add_months(value: date, months: int) -> date:
    month_index = value.month - 1 + months
    year = value.year + month_index // 12
    month = month_index % 12 + 1
    day = min(value.day, calendar.monthrange(year, month)[1])
    return date(year, month, day)


def agreement_from_offer(negotiation, offer) -> PaymentAgreement:
    agreement = PaymentAgreement(
        organization_id=negotiation.organization_id, client_id=negotiation.client_id,
        debt_id=negotiation.debt_id, title=f"Acordo da negociação {str(negotiation.id)[:8]}",
        status="active", payment_method="other", original_amount=offer.original_amount,
        negotiated_amount=offer.offered_amount, down_payment=offer.down_payment,
        installment_count=offer.installment_count, installment_amount=offer.installment_amount,
        first_due_date=offer.first_due_date,
        notes=f"Gerado automaticamente a partir da proposta {offer.sequence_number}.",
    )
    remaining = (Decimal(offer.offered_amount) - Decimal(offer.down_payment)).quantize(CENT)
    allocated = Decimal("0")
    for number in range(1, offer.installment_count + 1):
        amount = Decimal(offer.installment_amount).quantize(CENT, rounding=ROUND_HALF_UP)
        if number == offer.installment_count:
            amount = (remaining - allocated).quantize(CENT, rounding=ROUND_HALF_UP)
        if amount <= 0:
            amount = Decimal(offer.installment_amount).quantize(CENT, rounding=ROUND_HALF_UP)
        allocated += amount
        agreement.installments.append(PaymentInstallment(
            organization_id=negotiation.organization_id, client_id=negotiation.client_id,
            installment_number=number, due_date=add_months(offer.first_due_date, number - 1),
            amount=amount, status="pending", paid_amount=Decimal("0"),
        ))
    return agreement
