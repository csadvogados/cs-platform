import uuid
from datetime import date
from decimal import Decimal

from pydantic import BaseModel, Field, model_validator


class PaymentPlanSimulationCreate(BaseModel):
    debt_ids: list[uuid.UUID] | None = None
    discount_percentages: list[Decimal] = Field(
        default_factory=lambda: [Decimal("0"), Decimal("10"), Decimal("20")],
        min_length=1,
        max_length=6,
    )
    installment_terms: list[int] = Field(
        default_factory=lambda: [12, 24, 36, 48, 60],
        min_length=1,
        max_length=12,
    )
    annual_interest_rate: Decimal = Field(default=Decimal("0"), ge=0, le=100)
    down_payment: Decimal = Field(default=Decimal("0"), ge=0, max_digits=14, decimal_places=2)
    maximum_installment: Decimal | None = Field(default=None, gt=0, max_digits=14, decimal_places=2)
    minimum_installment: Decimal = Field(default=Decimal("50"), gt=0, max_digits=14, decimal_places=2)
    first_due_date: date | None = None

    @model_validator(mode="after")
    def validate_options(self):
        if any(term < 1 or term > 600 for term in self.installment_terms):
            raise ValueError("Os prazos devem estar entre 1 e 600 meses")
        if any(discount < 0 or discount > 100 for discount in self.discount_percentages):
            raise ValueError("Os descontos devem estar entre 0% e 100%")
        return self


class PaymentPlanScenarioRead(BaseModel):
    rank: int
    term_months: int
    discount_percentage: Decimal
    annual_interest_rate: Decimal
    original_amount: Decimal
    negotiated_amount: Decimal
    down_payment: Decimal
    financed_amount: Decimal
    installment_amount: Decimal
    total_payable: Decimal
    total_interest: Decimal
    first_due_date: date
    last_due_date: date
    capacity_usage_percentage: Decimal
    sustainable: bool
    score: int
    recommendation: str
    warnings: list[str]


class PaymentPlanSimulationRead(BaseModel):
    client_id: uuid.UUID
    organization_id: uuid.UUID
    selected_debt_ids: list[uuid.UUID]
    total_debt_amount: Decimal
    calculated_payment_capacity: Decimal
    applied_payment_limit: Decimal
    minimum_existential_reference: Decimal
    data_quality_score: int
    scenarios: list[PaymentPlanScenarioRead]
    rejected_scenarios: int
    warnings: list[str]
