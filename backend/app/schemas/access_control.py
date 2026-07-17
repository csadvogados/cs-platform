from __future__ import annotations

import uuid
from datetime import datetime
from pydantic import BaseModel, ConfigDict, EmailStr, Field

class PermissionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    code: str
    name: str
    module: str
    description: str | None = None

class RoleCreate(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    slug: str = Field(pattern=r"^[a-z0-9_-]+$", min_length=2, max_length=80)
    description: str | None = Field(default=None, max_length=1000)
    permission_codes: list[str] = []

class RoleUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=100)
    description: str | None = Field(default=None, max_length=1000)
    is_active: bool | None = None
    permission_codes: list[str] | None = None

class RoleRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    organization_id: uuid.UUID
    name: str
    slug: str
    description: str | None
    is_system: bool
    is_active: bool
    permissions: list[PermissionRead] = []

class InvitationCreate(BaseModel):
    email: EmailStr
    full_name: str = Field(min_length=3, max_length=200)
    role_id: uuid.UUID | None = None
    expires_in_hours: int = Field(default=72, ge=1, le=720)

class InvitationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    organization_id: uuid.UUID
    email: EmailStr
    full_name: str
    role_id: uuid.UUID | None
    expires_at: datetime
    accepted_at: datetime | None
    revoked_at: datetime | None
    created_at: datetime

class InvitationCreated(InvitationRead):
    token: str

class InvitationAccept(BaseModel):
    token: str = Field(min_length=20)
    password: str = Field(min_length=12, max_length=128)

class SessionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    user_id: uuid.UUID
    ip_address: str | None
    user_agent: str | None
    last_activity_at: datetime
    expires_at: datetime
    revoked_at: datetime | None
    created_at: datetime
