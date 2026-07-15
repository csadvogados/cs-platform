import uuid
from pydantic import BaseModel, ConfigDict, EmailStr, Field

class UserCreate(BaseModel):
    full_name: str = Field(min_length=3, max_length=200)
    email: EmailStr
    password: str = Field(min_length=10, max_length=128)
    role: str = "team"

class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    organization_id: uuid.UUID
    full_name: str
    email: EmailStr
    role: str
    status: str
    is_superuser: bool
