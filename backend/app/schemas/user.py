import uuid
from datetime import datetime
from pydantic import BaseModel, ConfigDict, EmailStr, Field

ALLOWED_ROLES = {"admin", "supervisor", "advogado", "negociador", "financeiro", "atendimento"}

class UserCreate(BaseModel):
    full_name: str = Field(min_length=3, max_length=200)
    email: EmailStr
    password: str = Field(min_length=12, max_length=128)
    role: str = "atendimento"
    role_ids: list[uuid.UUID] = []

class UserUpdate(BaseModel):
    full_name: str | None = Field(default=None, min_length=3, max_length=200)
    role: str | None = None
    status: str | None = None
    role_ids: list[uuid.UUID] | None = None

class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    organization_id: uuid.UUID
    full_name: str
    email: EmailStr
    role: str
    status: str
    is_superuser: bool
    must_change_password: bool
    failed_login_attempts: int
    locked_until: datetime | None
    last_login_at: datetime | None
    deleted_at: datetime | None

class UserPage(BaseModel):
    items: list[UserRead]
    total: int
    page: int
    page_size: int
