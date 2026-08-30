import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

DocumentStatus = Literal["pending", "validated", "rejected"]


class DocumentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    organization_id: uuid.UUID
    client_id: uuid.UUID
    uploaded_by_id: uuid.UUID | None
    validated_by_id: uuid.UUID | None
    category: str
    filename: str
    content_type: str
    size_bytes: int
    status: DocumentStatus
    validation_notes: str | None
    validated_at: datetime | None
    created_at: datetime


class DocumentValidation(BaseModel):
    status: Literal["validated", "rejected"]
    notes: str | None = Field(default=None, max_length=4000)


class JudicialChecklist(BaseModel):
    client_id: uuid.UUID
    required_categories: list[str]
    validated_categories: list[str]
    missing_categories: list[str]
    rejected_categories: list[str]
    ready: bool
