from datetime import date, datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

CRMStage = Literal["lead", "qualified", "proposal", "negotiation", "won", "lost"]
TaskStatus = Literal["pending", "in_progress", "completed", "cancelled"]
TaskPriority = Literal["low", "normal", "high", "urgent"]
InteractionType = Literal["call", "email", "meeting", "message", "note", "other"]


class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class ContactCreate(BaseModel):
    client_id: UUID | None = None
    name: str = Field(min_length=2, max_length=200)
    email: str | None = Field(default=None, max_length=320)
    phone: str | None = Field(default=None, max_length=40)
    position: str | None = Field(default=None, max_length=120)
    notes: str | None = Field(default=None, max_length=5000)

    @field_validator("name")
    @classmethod
    def normalize_name(cls, value: str) -> str:
        return " ".join(value.split())

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: str | None) -> str | None:
        if value is None:
            return None
        value = value.strip().lower()
        if "@" not in value or value.startswith("@") or value.endswith("@"):
            raise ValueError("E-mail inválido")
        return value


class ContactUpdate(BaseModel):
    client_id: UUID | None = None
    name: str | None = Field(default=None, min_length=2, max_length=200)
    email: str | None = Field(default=None, max_length=320)
    phone: str | None = Field(default=None, max_length=40)
    position: str | None = Field(default=None, max_length=120)
    notes: str | None = Field(default=None, max_length=5000)


class ContactRead(ContactCreate, ORMModel):
    id: UUID
    organization_id: UUID
    created_at: datetime
    updated_at: datetime


class InteractionCreate(BaseModel):
    client_id: UUID
    interaction_type: InteractionType
    subject: str = Field(min_length=2, max_length=200)
    description: str | None = Field(default=None, max_length=10000)
    occurred_at: datetime


class InteractionRead(InteractionCreate, ORMModel):
    id: UUID
    organization_id: UUID
    user_id: UUID | None = None
    created_at: datetime
    updated_at: datetime


class OpportunityCreate(BaseModel):
    client_id: UUID
    owner_id: UUID | None = None
    title: str = Field(min_length=2, max_length=200)
    stage: CRMStage = "lead"
    estimated_value: float = Field(default=0, ge=0, le=999999999999)
    probability: int = Field(default=0, ge=0, le=100)
    expected_close_date: date | None = None
    notes: str | None = Field(default=None, max_length=10000)


class OpportunityUpdate(BaseModel):
    client_id: UUID | None = None
    title: str | None = Field(default=None, min_length=2, max_length=200)
    stage: CRMStage | None = None
    estimated_value: float | None = Field(default=None, ge=0, le=999999999999)
    probability: int | None = Field(default=None, ge=0, le=100)
    expected_close_date: date | None = None
    notes: str | None = Field(default=None, max_length=10000)
    owner_id: UUID | None = None


class OpportunityRead(OpportunityCreate, ORMModel):
    id: UUID
    organization_id: UUID
    created_at: datetime
    updated_at: datetime


class TaskCreate(BaseModel):
    client_id: UUID | None = None
    opportunity_id: UUID | None = None
    assigned_to_id: UUID | None = None
    title: str = Field(min_length=2, max_length=200)
    description: str | None = Field(default=None, max_length=10000)
    status: TaskStatus = "pending"
    priority: TaskPriority = "normal"
    due_at: datetime | None = None


class TaskUpdate(BaseModel):
    client_id: UUID | None = None
    opportunity_id: UUID | None = None
    assigned_to_id: UUID | None = None
    title: str | None = Field(default=None, min_length=2, max_length=200)
    description: str | None = Field(default=None, max_length=10000)
    status: TaskStatus | None = None
    priority: TaskPriority | None = None
    due_at: datetime | None = None


class TaskRead(TaskCreate, ORMModel):
    id: UUID
    organization_id: UUID
    completed_at: datetime | None = None
    created_at: datetime
    updated_at: datetime


class CRMSummary(BaseModel):
    contacts: int
    interactions: int
    opportunities: int
    open_pipeline_value: float
    weighted_pipeline_value: float
    pending_tasks: int
    overdue_tasks: int
