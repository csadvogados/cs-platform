import uuid

from pydantic import BaseModel, ConfigDict, EmailStr, Field


ALLOWED_ROLES = {
    "admin",
    "supervisor",
    "advogado",
    "negociador",
    "financeiro",
    "atendimento",
}


class UserCreate(BaseModel):
    full_name: str = Field(min_length=3, max_length=200)
    email: EmailStr
    password: str = Field(min_length=12, max_length=128)
    role: str = "atendimento"


class UserUpdate(BaseModel):
    full_name: str | None = Field(
        default=None,
        min_length=3,
        max_length=200,
    )
    role: str | None = None
    status: str | None = None


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
