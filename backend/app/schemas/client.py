import re, uuid
from datetime import date
from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator
from app.models.enums import ClientStatus

class ClientBase(BaseModel):
    full_name: str = Field(min_length=3, max_length=200)
    cpf: str
    rg: str | None = None
    birth_date: date | None = None
    profession: str | None = None
    email: EmailStr | None = None
    phone: str | None = None
    city: str | None = None
    state: str | None = Field(default=None, min_length=2, max_length=2)
    status: ClientStatus = ClientStatus.LEAD
    person_natural: bool = True
    good_faith_declared: bool | None = None
    can_pay_without_harming_basics: bool | None = None
    notes: str | None = None
    assigned_user_id: uuid.UUID | None = None

    @field_validator("cpf")
    @classmethod
    def normalize_cpf(cls, value: str) -> str:
        digits = re.sub(r"\D", "", value)
        if len(digits) != 11 or digits == digits[0] * 11:
            raise ValueError("CPF deve conter 11 dígitos válidos estruturalmente")
        return digits

    @field_validator("state")
    @classmethod
    def normalize_state(cls, value: str | None) -> str | None:
        return value.upper() if value else value

class ClientCreate(ClientBase):
    pass

class ClientUpdate(BaseModel):
    full_name: str | None = Field(default=None, min_length=3, max_length=200)
    profession: str | None = None
    email: EmailStr | None = None
    phone: str | None = None
    city: str | None = None
    state: str | None = Field(default=None, min_length=2, max_length=2)
    status: ClientStatus | None = None
    good_faith_declared: bool | None = None
    can_pay_without_harming_basics: bool | None = None
    notes: str | None = None
    assigned_user_id: uuid.UUID | None = None

class ClientRead(ClientBase):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    organization_id: uuid.UUID


class ClientImportPreviewRow(BaseModel):
    line: int
    valid: bool
    duplicate: bool = False
    display_name: str | None = None
    display_cpf: str | None = None
    data: ClientCreate | None = None
    errors: list[str] = Field(default_factory=list)


class ClientImportPreview(BaseModel):
    filename: str
    total_rows: int
    valid_rows: int
    invalid_rows: int
    duplicate_rows: int
    rows: list[ClientImportPreviewRow]


class ClientImportRequest(BaseModel):
    source_filename: str | None = Field(default=None, max_length=255)
    clients: list[ClientCreate] = Field(min_length=1, max_length=500)


class ClientImportResult(BaseModel):
    imported: int
    client_ids: list[uuid.UUID]
