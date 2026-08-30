from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field
from typing import Literal

from app.models.recovery import RecoveryCaseSource, RecoveryCaseStage, RecoveryCaseStatus


class RecoveryCaseCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    client_id: uuid.UUID
    source: RecoveryCaseSource = RecoveryCaseSource.MANUAL
    assigned_user_id: uuid.UUID | None = None
    notes: str | None = Field(default=None, max_length=4000)


class RecoveryCaseUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    assigned_user_id: uuid.UUID | None = None
    notes: str | None = Field(default=None, max_length=4000)
    stage: RecoveryCaseStage | None = None
    version: int = Field(ge=1)


class RecoveryCaseTransition(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: RecoveryCaseStatus
    stage: RecoveryCaseStage | None = None
    reason: str | None = Field(default=None, max_length=1000)
    version: int = Field(ge=1)


class RecoveryCaseRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    organization_id: uuid.UUID
    client_id: uuid.UUID
    case_number: str
    status: RecoveryCaseStatus
    stage: RecoveryCaseStage
    source: RecoveryCaseSource
    assigned_user_id: uuid.UUID | None
    opened_at: datetime | None
    closed_at: datetime | None
    closure_reason: str | None
    notes: str | None
    version: int
    created_at: datetime
    updated_at: datetime


class RecoveryCasePage(BaseModel):
    items: list[RecoveryCaseRead]
    total: int = Field(ge=0)
    page: int = Field(ge=1)
    page_size: int = Field(ge=1, le=100)
    pages: int = Field(ge=0)


JudicialProcessStatus = Literal["filed", "awaiting_decision", "hearing_scheduled", "decision_issued", "appeal", "closed"]
JudicialEventType = Literal["filing", "movement", "deadline", "hearing", "decision", "appeal", "note"]


class JudicialProcessUpsert(BaseModel):
    model_config = ConfigDict(extra="forbid")
    process_number: str = Field(min_length=5, max_length=40)
    court: str = Field(min_length=2, max_length=160)
    district: str | None = Field(default=None, max_length=160)
    division: str | None = Field(default=None, max_length=160)
    filed_at: datetime | None = None
    status: JudicialProcessStatus = "filed"
    next_deadline: datetime | None = None
    notes: str | None = Field(default=None, max_length=4000)
    version: int | None = Field(default=None, ge=1)


class JudicialProcessEventCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    event_date: datetime
    event_type: JudicialEventType
    title: str = Field(min_length=2, max_length=200)
    description: str | None = Field(default=None, max_length=4000)


class JudicialDeadlineComplete(BaseModel):
    model_config = ConfigDict(extra="forbid")
    completed_at: datetime
    notes: str | None = Field(default=None, max_length=1000)
    version: int = Field(ge=1)


class JudicialProcessEventRead(JudicialProcessEventCreate):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    created_by_user_id: uuid.UUID | None
    created_at: datetime


class JudicialProcessRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    organization_id: uuid.UUID
    recovery_case_id: uuid.UUID
    process_number: str
    court: str
    district: str | None
    division: str | None
    filed_at: datetime | None
    status: JudicialProcessStatus
    next_deadline: datetime | None
    notes: str | None
    version: int
    events: list[JudicialProcessEventRead] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime
