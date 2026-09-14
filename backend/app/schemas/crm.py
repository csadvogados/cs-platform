from datetime import date, datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.schemas.client import ClientRead


CRMStage = Literal["new", "contacted", "qualified", "proposal", "converted", "lost"]
TaskStatus = Literal["pending", "in_progress", "completed", "cancelled"]
TaskPriority = Literal["low", "normal", "high", "urgent"]
InteractionType = Literal["call", "email", "meeting", "message", "note", "other"]
CaseStatus = Literal[
    "lead",
    "triage",
    "contracted",
    "documentation",
    "diagnosis",
    "negotiation",
    "ombudsman",
    "consumidor_gov",
    "legal_review",
    "judicial",
    "settled",
    "closed",
    "cancelled",
]


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
    opportunity_id: UUID | None = None
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
    stage: CRMStage = "new"
    source: str | None = Field(default=None, max_length=80)
    service: str | None = Field(default=None, max_length=120)
    estimated_value: float = Field(default=0, ge=0, le=999999999999)
    probability: int = Field(default=0, ge=0, le=100)
    expected_close_date: date | None = None
    next_contact_at: datetime | None = None
    lost_reason: str | None = Field(default=None, max_length=5000)
    notes: str | None = Field(default=None, max_length=10000)

    @field_validator("source", "service")
    @classmethod
    def normalize_optional_text(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = " ".join(value.split())
        return normalized or None


class OpportunityUpdate(BaseModel):
    client_id: UUID | None = None
    title: str | None = Field(default=None, min_length=2, max_length=200)
    stage: CRMStage | None = None
    source: str | None = Field(default=None, max_length=80)
    service: str | None = Field(default=None, max_length=120)
    estimated_value: float | None = Field(default=None, ge=0, le=999999999999)
    probability: int | None = Field(default=None, ge=0, le=100)
    expected_close_date: date | None = None
    next_contact_at: datetime | None = None
    lost_reason: str | None = Field(default=None, max_length=5000)
    notes: str | None = Field(default=None, max_length=10000)
    owner_id: UUID | None = None


class OpportunityRead(OpportunityCreate, ORMModel):
    id: UUID
    organization_id: UUID
    stage_changed_at: datetime
    converted_at: datetime | None = None
    lost_at: datetime | None = None
    created_at: datetime
    updated_at: datetime


class OpportunityStageChange(BaseModel):
    stage: CRMStage
    note: str | None = Field(default=None, max_length=5000)
    lost_reason: str | None = Field(default=None, max_length=5000)


class OpportunityStageHistoryRead(ORMModel):
    id: UUID
    organization_id: UUID
    opportunity_id: UUID
    changed_by_id: UUID | None = None
    from_stage: str | None = None
    to_stage: str
    note: str | None = None
    changed_at: datetime


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


class CaseRead(ORMModel):
    id: UUID
    organization_id: UUID
    client_id: UUID
    opportunity_id: UUID | None = None
    assigned_user_id: UUID | None = None
    service: str
    title: str
    status: str
    notes: str | None = None
    created_at: datetime
    updated_at: datetime


class OpportunityConvertRequest(BaseModel):
    create_case: bool = True
    case_status: CaseStatus = "triage"
    case_title: str | None = Field(default=None, min_length=2, max_length=250)
    note: str | None = Field(default=None, max_length=5000)


class OpportunityConvertResponse(BaseModel):
    opportunity: OpportunityRead
    client: ClientRead
    case: CaseRead | None = None


class PipelineCard(BaseModel):
    opportunity_id: UUID
    client_id: UUID
    client_name: str
    phone: str | None = None
    title: str
    stage: CRMStage
    source: str | None = None
    service: str | None = None
    owner_id: UUID | None = None
    owner_name: str | None = None
    next_contact_at: datetime | None = None
    estimated_value: float
    probability: int
    updated_at: datetime


class PipelineColumn(BaseModel):
    stage: CRMStage
    label: str
    count: int
    items: list[PipelineCard]


class LeadDetail(BaseModel):
    opportunity: OpportunityRead
    client: ClientRead
    interactions: list[InteractionRead]
    tasks: list[TaskRead]
    history: list[OpportunityStageHistoryRead]
    case: CaseRead | None = None


class CRMSummary(BaseModel):
    contacts: int
    interactions: int
    opportunities: int
    open_pipeline_value: float
    weighted_pipeline_value: float
    pending_tasks: int
    overdue_tasks: int


class CRMDashboard(BaseModel):
    leads_new: int
    leads_in_progress: int
    leads_qualified: int
    open_proposals: int
    leads_converted: int
    leads_lost: int
    conversion_rate: float
    avg_days_to_conversion: float | None = None
    estimated_proposal_revenue: float
    contracted_revenue: float
    overdue_followups: int
