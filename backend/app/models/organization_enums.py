from __future__ import annotations
from enum import StrEnum

class OrganizationStatus(StrEnum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    PENDING = "pending"

class OrganizationType(StrEnum):
    LAW_FIRM = "law_firm"
    CONSULTING = "consulting"
    COMPANY = "company"
    INDIVIDUAL = "individual"
    OTHER = "other"

class OrganizationPlan(StrEnum):
    STARTER = "starter"
    PROFESSIONAL = "professional"
    ENTERPRISE = "enterprise"
    CUSTOM = "custom"

class LicenseStatus(StrEnum):
    ACTIVE = "active"
    TRIAL = "trial"
    EXPIRED = "expired"
    SUSPENDED = "suspended"
    CANCELED = "canceled"

class AddressType(StrEnum):
    HEADQUARTERS = "headquarters"
    BRANCH = "branch"
    BILLING = "billing"
    CORRESPONDENCE = "correspondence"
    OTHER = "other"
