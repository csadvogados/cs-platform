from datetime import date, datetime
from decimal import Decimal
from typing import Literal
from uuid import UUID
import re

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator, model_validator

LeadStatus = Literal["NOVO", "CONTATADO", "QUALIFICADO", "PROPOSTA", "CONVERTIDO", "PERDIDO"]
LeadPriority = Literal["BAIXA", "NORMAL", "ALTA", "URGENTE"]
InterestLevel = Literal["BAIXO", "MEDIO", "ALTO"]
LostReason = Literal["SEM_INTERESSE", "HONORARIOS", "NAO_RESPONDEU", "OUTRO_ADVOGADO", "SEM_VIABILIDADE", "DOCUMENTACAO_INSUFICIENTE", "FORA_ATUACAO", "ATENDIMENTO_INCOMPLETO", "OUTRO"]
InteractionType = Literal["WHATSAPP", "LIGACAO", "EMAIL", "REUNIAO", "PRESENCIAL", "VIDEOCONFERENCIA", "PROPOSTA", "DOCUMENTO", "NOTA", "OUTRO", "STATUS"]


class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class CatalogRead(ORMModel):
    id: UUID
    code: str
    name: str
    active: bool


class LeadBase(BaseModel):
    full_name: str = Field(min_length=3, max_length=200)
    cpf: str | None = None
    phone: str | None = Field(default=None, max_length=30)
    whatsapp: str | None = Field(default=None, max_length=30)
    email: EmailStr | None = None
    city: str | None = Field(default=None, max_length=120)
    state: str | None = Field(default=None, min_length=2, max_length=2)
    birth_date: date | None = None
    source_id: UUID
    source_detail: str | None = Field(default=None, max_length=200)
    service_type_id: UUID
    campaign: str | None = Field(default=None, max_length=160)
    owner_id: UUID | None = None
    status: LeadStatus = "NOVO"
    priority: LeadPriority = "NORMAL"
    initial_notes: str | None = Field(default=None, max_length=5000)
    has_legal_demand: bool | None = None
    urgent: bool | None = None
    has_lawyer: bool | None = None
    has_ongoing_case: bool | None = None
    had_previous_proposal: bool | None = None
    can_afford: bool | None = None
    interest_level: InterestLevel | None = None
    approximate_debt: Decimal | None = Field(default=None, ge=0)
    approximate_creditors: int | None = Field(default=None, ge=0)
    monthly_income: Decimal | None = Field(default=None, ge=0)
    income_commitment_percent: Decimal | None = Field(default=None, ge=0, le=100)
    delinquency_status: str | None = Field(default=None, max_length=100)
    is_negative_listed: bool | None = None
    has_existing_lawsuit: bool | None = None

    @field_validator("full_name")
    @classmethod
    def normalize_name(cls, value): return " ".join(value.split())

    @field_validator("cpf")
    @classmethod
    def normalize_cpf(cls, value):
        if not value: return None
        digits = re.sub(r"\D", "", value)
        if len(digits) != 11 or digits == digits[0] * 11: raise ValueError("CPF deve conter 11 dígitos válidos estruturalmente")
        return digits

    @field_validator("state")
    @classmethod
    def normalize_state(cls, value): return value.upper() if value else value

    @model_validator(mode="after")
    def validate_contact(self):
        if not any([self.phone, self.whatsapp, self.email]):
            raise ValueError("Informe ao menos telefone, WhatsApp ou e-mail")
        return self


class LeadCreate(LeadBase): pass


class LeadUpdate(BaseModel):
    full_name: str | None = Field(default=None, min_length=3, max_length=200)
    cpf: str | None = None
    phone: str | None = Field(default=None, max_length=30)
    whatsapp: str | None = Field(default=None, max_length=30)
    email: EmailStr | None = None
    city: str | None = Field(default=None, max_length=120)
    state: str | None = Field(default=None, min_length=2, max_length=2)
    birth_date: date | None = None
    source_id: UUID | None = None
    source_detail: str | None = Field(default=None, max_length=200)
    service_type_id: UUID | None = None
    campaign: str | None = Field(default=None, max_length=160)
    owner_id: UUID | None = None
    priority: LeadPriority | None = None
    initial_notes: str | None = Field(default=None, max_length=5000)
    has_legal_demand: bool | None = None
    urgent: bool | None = None
    has_lawyer: bool | None = None
    has_ongoing_case: bool | None = None
    had_previous_proposal: bool | None = None
    can_afford: bool | None = None
    interest_level: InterestLevel | None = None
    approximate_debt: Decimal | None = Field(default=None, ge=0)
    approximate_creditors: int | None = Field(default=None, ge=0)
    monthly_income: Decimal | None = Field(default=None, ge=0)
    income_commitment_percent: Decimal | None = Field(default=None, ge=0, le=100)
    delinquency_status: str | None = Field(default=None, max_length=100)
    is_negative_listed: bool | None = None
    has_existing_lawsuit: bool | None = None


class LeadRead(LeadBase, ORMModel):
    id: UUID
    organization_id: UUID
    lost_reason: str | None
    lost_notes: str | None
    converted_at: datetime | None
    client_id: UUID | None
    recovery_case_id: UUID | None
    created_at: datetime
    updated_at: datetime


class StatusChange(BaseModel):
    status: LeadStatus
    lost_reason: LostReason | None = None
    lost_notes: str | None = Field(default=None, max_length=2000)

    @model_validator(mode="after")
    def lost_requires_reason(self):
        if self.status == "PERDIDO" and not self.lost_reason: raise ValueError("Motivo é obrigatório para lead perdido")
        return self


class InteractionCreate(BaseModel):
    interaction_type: InteractionType
    description: str = Field(min_length=2, max_length=10000)
    occurred_at: datetime
    next_action: str | None = Field(default=None, max_length=300)
    next_action_at: datetime | None = None
    assigned_to_id: UUID | None = None


class InteractionRead(ORMModel):
    id: UUID; lead_id: UUID; user_id: UUID | None; interaction_type: str; description: str; occurred_at: datetime; created_at: datetime


class TaskCreate(BaseModel):
    description: str = Field(min_length=2, max_length=300)
    due_at: datetime
    assigned_to_id: UUID | None = None
    status: Literal["PENDENTE", "CONCLUIDA", "CANCELADA"] = "PENDENTE"
    priority: LeadPriority = "NORMAL"


class TaskRead(TaskCreate, ORMModel):
    id: UUID; lead_id: UUID; completed_at: datetime | None; created_at: datetime


class ProposalCreate(BaseModel):
    fixed_value: Decimal = Field(default=Decimal("0"), ge=0)
    down_payment: Decimal = Field(default=Decimal("0"), ge=0)
    installments: int = Field(default=1, ge=1, le=120)
    installment_value: Decimal = Field(default=Decimal("0"), ge=0)
    success_percentage: Decimal = Field(default=Decimal("0"), ge=0, le=100)
    valid_until: date | None = None
    sent_at: datetime | None = None
    status: Literal["RASCUNHO", "ENVIADA", "ACEITA", "RECUSADA", "EXPIRADA"] = "RASCUNHO"
    notes: str | None = Field(default=None, max_length=5000)


class ProposalRead(ProposalCreate, ORMModel):
    id: UUID; lead_id: UUID; created_at: datetime


class ProposalUpdate(BaseModel):
    status: Literal["RASCUNHO", "ENVIADA", "ACEITA", "RECUSADA", "EXPIRADA"]


class ContractCreate(BaseModel):
    template_id: UUID | None = None
    title: str | None = Field(default=None, min_length=3, max_length=200)
    content: str | None = Field(default=None, max_length=50000)
    notes: str | None = Field(default=None, max_length=5000)


class ContractStatusUpdate(BaseModel):
    status: Literal["EM_REVISAO", "APROVADO", "ENVIADO", "ASSINADO", "CANCELADO"]
    signature_reference: str | None = Field(default=None, max_length=300)

    @model_validator(mode="after")
    def signed_requires_reference(self):
        if self.status == "ASSINADO" and not self.signature_reference:
            raise ValueError("Informe a referência da assinatura")
        return self


class ContractRead(ORMModel):
    id: UUID; organization_id: UUID; lead_id: UUID; proposal_id: UUID; client_id: UUID
    template_id: UUID | None
    contract_number: str; title: str; content: str; status: str; version: int
    approved_by_id: UUID | None; approved_at: datetime | None; sent_at: datetime | None
    signature_due_at: date | None; delivery_channel: str | None; delivery_recipient: str | None
    signed_at: datetime | None; signature_reference: str | None; notes: str | None
    created_at: datetime; updated_at: datetime


class ContractListItem(ContractRead):
    client_name: str
    lead_name: str


class ContractSummary(BaseModel):
    total: int = 0
    draft: int = 0
    awaiting_approval: int = 0
    awaiting_signature: int = 0
    signed: int = 0
    cancelled: int = 0
    overdue_signatures: int = 0


class ContractDeliveryCreate(BaseModel):
    channel: Literal["EMAIL", "WHATSAPP", "OUTRO"]
    recipient: str = Field(min_length=3, max_length=320)
    signature_due_at: date
    notes: str | None = Field(default=None, max_length=2000)


class ContractDeliveryRead(ContractDeliveryCreate, ORMModel):
    id: UUID
    contract_id: UUID
    sent_by_id: UUID | None
    sent_at: datetime
    created_at: datetime


class ContractTemplateCreate(BaseModel):
    name: str = Field(min_length=3, max_length=150)
    title: str = Field(min_length=3, max_length=200)
    content: str = Field(min_length=20, max_length=50000)
    service_type_id: UUID | None = None
    active: bool = True


class ContractTemplateUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=3, max_length=150)
    title: str | None = Field(default=None, min_length=3, max_length=200)
    content: str | None = Field(default=None, min_length=20, max_length=50000)
    service_type_id: UUID | None = None
    active: bool | None = None


class ContractTemplateRead(ContractTemplateCreate, ORMModel):
    id: UUID
    organization_id: UUID
    created_by_id: UUID | None
    created_at: datetime
    updated_at: datetime


class ConvertLead(BaseModel):
    confirm_duplicate_client_id: UUID | None = None
    create_recovery_case: bool = False


class ConversionResult(BaseModel):
    lead: LeadRead
    client_id: UUID
    recovery_case_id: UUID | None = None
    possible_duplicates: list[UUID] = Field(default_factory=list)


class DashboardRead(BaseModel):
    new_leads: int; in_progress: int; qualified: int; open_proposals: int; converted: int; lost: int
    conversion_rate: float; average_conversion_days: float; estimated_revenue: float; contracted_revenue: float
    overdue_tasks: int = 0; proposals_expiring: int = 0; leads_without_next_action: int = 0


class ReportRow(BaseModel):
    key: str; name: str; leads: int; converted: int; lost: int; proposals: int = 0; conversion_rate: float


class LeadDistributionCreate(BaseModel):
    user_ids: list[UUID] = Field(min_length=1, max_length=100)


class LeadDistributionOwnerRead(BaseModel):
    user_id: UUID
    user_name: str
    assigned: int = 0


class LeadDistributionRead(BaseModel):
    assigned: int = 0
    remaining_unassigned: int = 0
    owners: list[LeadDistributionOwnerRead] = Field(default_factory=list)


class LeadTeamPerformanceRead(BaseModel):
    user_id: UUID | None = None
    user_name: str
    assigned_leads: int = 0
    active_leads: int = 0
    converted: int = 0
    lost: int = 0
    overdue_tasks: int = 0
    leads_without_next_action: int = 0
    conversion_rate: float = 0
