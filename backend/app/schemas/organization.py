from __future__ import annotations
from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, ConfigDict, EmailStr, Field, HttpUrl, field_validator
from app.models.organization_enums import (
    AddressType, LicenseStatus, OrganizationPlan, OrganizationStatus, OrganizationType
)
from app.validators.organization import (
    normalize_brazilian_tax_id, normalize_hex_color, normalize_phone,
    normalize_postal_code, normalize_state_code, validate_brazilian_tax_id
)

class OrganizationAddressCreate(BaseModel):
    address_type: AddressType = AddressType.HEADQUARTERS
    postal_code: str | None = None
    street: str | None = None
    number: str | None = None
    complement: str | None = None
    district: str | None = None
    city: str | None = None
    state: str | None = None
    country: str = "BR"
    is_primary: bool = False

    @field_validator("postal_code")
    @classmethod
    def postal(cls, v): return normalize_postal_code(v)

    @field_validator("state")
    @classmethod
    def state_code(cls, v): return normalize_state_code(v)

class OrganizationSettingsCreate(BaseModel):
    timezone: str = "America/Sao_Paulo"
    language: str = "pt-BR"
    currency: str = "BRL"
    date_format: str = "DD/MM/YYYY"
    allow_client_portal: bool = False
    allow_external_integrations: bool = False
    require_mfa_for_admins: bool = False

class OrganizationBrandingCreate(BaseModel):
    public_name: str | None = None
    logo_url: HttpUrl | None = None
    favicon_url: HttpUrl | None = None
    primary_color: str = "#0F172A"
    secondary_color: str = "#2563EB"

    @field_validator("primary_color", "secondary_color")
    @classmethod
    def color(cls, v): return normalize_hex_color(v)

class OrganizationLicenseCreate(BaseModel):
    plan: OrganizationPlan = OrganizationPlan.STARTER
    status: LicenseStatus = LicenseStatus.TRIAL
    starts_at: datetime | None = None
    expires_at: datetime | None = None
    max_users: int = Field(default=5, ge=1)
    max_storage_mb: int = Field(default=1024, ge=1)

class OrganizationCreate(BaseModel):
    legal_name: str = Field(min_length=2, max_length=200)
    trade_name: str | None = None
    tax_id: str | None = None
    state_registration: str | None = None
    municipal_registration: str | None = None
    organization_type: OrganizationType = OrganizationType.LAW_FIRM
    email: EmailStr | None = None
    phone: str | None = None
    website: HttpUrl | None = None
    description: str | None = None
    status: OrganizationStatus = OrganizationStatus.ACTIVE
    is_system_default: bool = False
    settings: OrganizationSettingsCreate | None = None
    branding: OrganizationBrandingCreate | None = None
    license: OrganizationLicenseCreate | None = None
    addresses: list[OrganizationAddressCreate] = Field(default_factory=list)

    @field_validator("tax_id")
    @classmethod
    def tax(cls, v):
        n = normalize_brazilian_tax_id(v)
        if n and not validate_brazilian_tax_id(n):
            raise ValueError("CNPJ inválido.")
        return n

    @field_validator("phone")
    @classmethod
    def phone_value(cls, v): return normalize_phone(v)

class OrganizationUpdate(BaseModel):
    legal_name: str | None = None
    trade_name: str | None = None
    tax_id: str | None = None
    state_registration: str | None = None
    municipal_registration: str | None = None
    organization_type: OrganizationType | None = None
    email: EmailStr | None = None
    phone: str | None = None
    website: HttpUrl | None = None
    description: str | None = None
    status: OrganizationStatus | None = None
    is_system_default: bool | None = None

class OrganizationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    legal_name: str
    trade_name: str | None
    tax_id: str | None
    organization_type: str
    email: str | None
    phone: str | None
    status: str
    is_system_default: bool
    created_at: datetime
    updated_at: datetime
