from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class AuditEventRead(BaseModel):
    id: int
    user_id: uuid.UUID | None
    actor_name: str
    actor_email: str | None
    entity_type: str
    entity_id: uuid.UUID | None
    action: str
    details: dict[str, Any] | None
    occurred_at: datetime


class AuditPage(BaseModel):
    items: list[AuditEventRead]
    total: int = Field(ge=0)
    page: int = Field(ge=1)
    page_size: int = Field(ge=1)
    pages: int = Field(ge=0)
