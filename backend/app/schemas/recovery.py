from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

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
