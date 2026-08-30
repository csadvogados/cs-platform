import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

NegotiationStatus = Literal["open", "accepted", "rejected", "expired", "cancelled"]
OfferStatus = Literal["pending", "accepted", "rejected", "expired", "withdrawn"]


class NegotiationCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    recovery_case_id: uuid.UUID
    debt_id: uuid.UUID
    assigned_user_id: uuid.UUID | None = None
    channel: Literal["phone", "email", "whatsapp", "portal", "consumer_gov", "in_person", "other"] = "other"
    external_reference: str | None = Field(default=None, max_length=120)
    expires_at: datetime | None = None
    notes: str | None = Field(default=None, max_length=4000)


class NegotiationOfferCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    origin: Literal["creditor", "client", "system"]
    offered_amount: Decimal = Field(gt=0, max_digits=14, decimal_places=2)
    down_payment: Decimal = Field(default=Decimal("0"), ge=0, max_digits=14, decimal_places=2)
    installment_count: int = Field(ge=1, le=600)
    installment_amount: Decimal = Field(gt=0, max_digits=14, decimal_places=2)
    annual_interest_rate: Decimal = Field(default=Decimal("0"), ge=0, le=100)
    first_due_date: date
    valid_until: datetime | None = None
    notes: str | None = Field(default=None, max_length=4000)

    @model_validator(mode="after")
    def validate_amounts(self):
        if self.down_payment > self.offered_amount:
            raise ValueError("A entrada não pode superar o valor ofertado")
        return self


class NegotiationOfferDecision(BaseModel):
    model_config = ConfigDict(extra="forbid")
    status: Literal["accepted", "rejected", "withdrawn"]
    reason: str | None = Field(default=None, max_length=1000)


class NegotiationOfferRead(NegotiationOfferCreate):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    organization_id: uuid.UUID
    negotiation_id: uuid.UUID
    created_by_user_id: uuid.UUID
    sequence_number: int
    original_amount: Decimal
    sustainable: bool
    capacity_usage_percentage: Decimal
    engine_score: int
    engine_decision: Literal["accept", "counter", "reject", "manual_review"]
    engine_reason: str
    status: OfferStatus
    responded_at: datetime | None
    created_at: datetime
    updated_at: datetime


class NegotiationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    organization_id: uuid.UUID
    recovery_case_id: uuid.UUID
    client_id: uuid.UUID
    debt_id: uuid.UUID
    creditor_id: uuid.UUID | None
    assigned_user_id: uuid.UUID | None
    status: NegotiationStatus
    channel: str
    external_reference: str | None
    opened_at: datetime
    expires_at: datetime | None
    closed_at: datetime | None
    closure_reason: str | None
    notes: str | None
    version: int
    offers: list[NegotiationOfferRead] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime
