from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr


class IdentityOrganizationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    legal_name: str
    trade_name: str | None
    status: str


class IdentityRead(BaseModel):
    id: UUID
    organization_id: UUID
    full_name: str
    email: EmailStr
    role: str
    status: str
    is_superuser: bool
    must_change_password: bool
    permissions: list[str]
    organization: IdentityOrganizationRead
