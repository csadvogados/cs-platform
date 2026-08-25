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
InstallmentStatus = Literal["pending", "paid", "overdue", "cancelled"]
CollectionStatus = Literal["pending", "due_soon", "paid", "overdue", "cancelled"]
CollectionActionType = Literal["phone", "whatsapp", "email", "negotiation", "other"]
CollectionOutcome = Literal["contacted", "no_answer", "promise_to_pay", "refused", "other"]
CollectionPriority = Literal["low", "normal", "high", "urgent"]

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


class PaymentInstallmentRead(ORM):
    id: uuid.UUID
    organization_id: uuid.UUID
    client_id: uuid.UUID
    agreement_id: uuid.UUID
    installment_number: int
    due_date: date
    amount: Decimal
    status: InstallmentStatus
    paid_amount: Decimal
    paid_at: datetime | None
    payment_method: PaymentMethod | None
    payment_notes: str | None
    collection_assigned_user_id: uuid.UUID | None = None
    collection_priority: CollectionPriority = "normal"
    created_at: datetime
    updated_at: datetime


class InstallmentPaymentCreate(BaseModel):
    paid_amount: Decimal = Field(gt=0, max_digits=14, decimal_places=2)
    paid_at: datetime
    payment_method: PaymentMethod
    payment_notes: str | None = Field(default=None, max_length=10000)


class PaymentAgreementRead(PaymentAgreementCreate, ORM):
    id: uuid.UUID
    organization_id: uuid.UUID
    client_id: uuid.UUID
    created_at: datetime
    updated_at: datetime
    installments: list[PaymentInstallmentRead] = Field(default_factory=list)


class CollectionItemRead(BaseModel):
    id: uuid.UUID
    client_id: uuid.UUID
    client_name: str
    agreement_id: uuid.UUID
    agreement_title: str
    installment_number: int
    due_date: date
    amount: Decimal
    status: CollectionStatus
    paid_amount: Decimal
    paid_at: datetime | None
    payment_method: PaymentMethod | None
    action_count: int = 0
    last_contacted_at: datetime | None = None
    next_follow_up_at: datetime | None = None
    latest_outcome: CollectionOutcome | None = None
    follow_up_status: Literal["none", "overdue", "today", "upcoming"] = "none"
    latest_promise_date: date | None = None
    latest_promise_amount: Decimal | None = None
    promise_status: Literal["none", "overdue", "today", "upcoming"] = "none"
    assigned_user_id: uuid.UUID | None = None
    assigned_user_name: str | None = None
    priority: CollectionPriority = "normal"


class CollectionSummaryRead(BaseModel):
    open_count: int
    open_amount: Decimal
    overdue_count: int
    overdue_amount: Decimal
    due_soon_count: int
    due_soon_amount: Decimal
    paid_this_month_count: int
    paid_this_month_amount: Decimal
    follow_up_today_count: int = 0
    overdue_follow_up_count: int = 0
    upcoming_follow_up_count: int = 0
    open_promises_count: int = 0
    overdue_promises_count: int = 0
    urgent_count: int = 0
    unassigned_count: int = 0


class CollectionsRead(BaseModel):
    summary: CollectionSummaryRead
    items: list[CollectionItemRead]
    total: int


class CollectionAssignmentUpdate(BaseModel):
    assigned_user_id: uuid.UUID | None = None
    priority: CollectionPriority = "normal"


class CollectionTeamPerformanceRead(BaseModel):
    user_id: uuid.UUID
    user_name: str
    action_count: int = 0
    contacted_clients: int = 0
    promise_count: int = 0
    promise_amount: Decimal = Decimal("0")
    follow_up_count: int = 0


class CollectionReportRead(BaseModel):
    date_from: date
    date_to: date
    due_count: int = 0
    due_amount: Decimal = Decimal("0")
    received_count: int = 0
    received_amount: Decimal = Decimal("0")
    overdue_count: int = 0
    overdue_amount: Decimal = Decimal("0")
    action_count: int = 0
    contacted_clients: int = 0
    promise_count: int = 0
    promise_amount: Decimal = Decimal("0")
    recovery_rate: Decimal = Decimal("0")
    team: list[CollectionTeamPerformanceRead] = Field(default_factory=list)


class CollectionActionCreate(BaseModel):
    action_type: CollectionActionType
    outcome: CollectionOutcome
    contacted_at: datetime
    notes: str = Field(min_length=2, max_length=10000)
    promise_date: date | None = None
    promise_amount: Decimal | None = Field(default=None, gt=0, max_digits=14, decimal_places=2)
    next_follow_up_at: datetime | None = None

    @model_validator(mode="after")
    def validate_promise(self):
        if self.outcome == "promise_to_pay" and self.promise_date is None:
            raise ValueError("Informe a data prometida para pagamento")
        if self.outcome != "promise_to_pay":
            self.promise_date = None
            self.promise_amount = None
        return self


class CollectionActionRead(CollectionActionCreate, ORM):
    id: uuid.UUID
    organization_id: uuid.UUID
    client_id: uuid.UUID
    agreement_id: uuid.UUID
    installment_id: uuid.UUID
    created_by_user_id: uuid.UUID
    created_by_name: str
    created_at: datetime
    cancelled_at: datetime | None = None
    cancelled_by_user_id: uuid.UUID | None = None
    cancelled_by_name: str | None = None
    cancellation_reason: str | None = None


class CollectionActionCancel(BaseModel):
    reason: str = Field(min_length=5, max_length=1000)
