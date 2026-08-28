from datetime import datetime
from typing import Literal
import uuid

from pydantic import BaseModel, ConfigDict, Field


class NotificationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    notification_type: str
    priority: str
    title: str
    message: str
    target_view: str | None = None
    target_filter: str | None = None
    event_at: datetime
    read_at: datetime | None = None
    created_at: datetime


class NotificationPage(BaseModel):
    items: list[NotificationRead] = Field(default_factory=list)
    total: int = 0
    unread_count: int = 0
    critical_unread_count: int = 0


class NotificationStatusUpdate(BaseModel):
    read: bool


class NotificationPreferencesRead(BaseModel):
    tasks_enabled: bool = True
    collections_enabled: bool = True
    promises_enabled: bool = True
    goals_enabled: bool = True
    judicial_enabled: bool = True
    only_assigned_items: bool = False


class NotificationPreferencesUpdate(NotificationPreferencesRead):
    pass
