import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

PaymentMethod = Literal[
    "pix", "bank_slip", "bank_transfer", "cash", "credit_card",
    "debit_card", "automatic_debit", "other",
]
AgreementStatus = Literal["draft", "active", "completed", "defaulted", "cancelled"]

class ORM(BaseModel): model_config = ConfigDict(from_attributes=True)
class IncomeCreate(BaseModel):
    income_type: str
    description: str | None = None
    net_amount: Decimal = Field(ge=0)
    recurring: bool = True
class IncomeRead(IncomeCreate, ORM): id: uuid.UUID; client_id: uuid.UUID
class ExpenseCreate(BaseModel):
    category: str
    description: str | None = None
    amount: Decimal = Field(ge=0)
    essential: bool = True
    recurring: bool = True
class ExpenseRead(ExpenseCreate, ORM): id: uuid.UUID; client_id: uuid.UUID
class CreditorCreate(BaseModel):
    legal_name: str
    sac_phone: str | None = None
    sac_email: str | None = None
    ombudsman_phone: str | None = None
    ombudsman_email: str | None = None
    consumer_gov_enabled: bool = False
class CreditorRead(CreditorCreate, ORM): id: uuid.UUID; organization_id: uuid.UUID
class DebtCreate(BaseModel):
    creditor_id: uuid.UUID | None = None
    nature: str
    current_balance: Decimal = Field(default=0, ge=0)
    monthly_installment: Decimal = Field(default=0, ge=0)
    overdue: bool = False
class DebtRead(DebtCreate, ORM): id: uuid.UUID; organization_id: uuid.UUID; client_id: uuid.UUID


class PaymentAgreementCreate(BaseModel):
    debt_id: uuid.UUID | None = None
    title: str = Field(min_length=2, max_length=200)
    status: AgreementStatus = "active"
    payment_method: PaymentMethod
    original_amount: Decimal = Field(default=Decimal("0"), ge=0, max_digits=14, decimal_places=2)
    negotiated_amount: Decimal = Field(gt=0, max_digits=14, decimal_places=2)
    down_payment: Decimal = Field(default=Decimal("0"), ge=0, max_digits=14, decimal_places=2)
    installment_count: int = Field(default=1, ge=1, le=600)
    installment_amount: Decimal = Field(default=Decimal("0"), ge=0, max_digits=14, decimal_places=2)
    first_due_date: date | None = None
    notes: str | None = Field(default=None, max_length=10000)

    @model_validator(mode="after")
    def validate_amounts(self):
        if self.down_payment > self.negotiated_amount:
            raise ValueError("A entrada não pode ser maior que o valor negociado")
        return self


class PaymentAgreementRead(PaymentAgreementCreate, ORM):
    id: uuid.UUID
    organization_id: uuid.UUID
    client_id: uuid.UUID
    created_at: datetime
    updated_at: datetime
