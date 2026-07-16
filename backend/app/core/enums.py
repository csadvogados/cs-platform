"""
CS Platform Enterprise
Release v5.0.0 - TITANIUM
Pacote 01A - Foundation Core
Entrega 01A.3

Arquivo:
    backend/app/core/enums.py

Finalidade:
    Centralizar enumerações de domínio e infraestrutura, evitando strings
    livres, divergências de nomenclatura e validações duplicadas.
"""

from __future__ import annotations

from enum import Enum, StrEnum


class BaseStrEnum(StrEnum):
    """Base comum para enums textuais serializáveis em JSON."""

    @classmethod
    def values(cls) -> tuple[str, ...]:
        return tuple(member.value for member in cls)

    @classmethod
    def has_value(cls, value: str) -> bool:
        try:
            cls(value)
            return True
        except ValueError:
            return False


class Environment(BaseStrEnum):
    DEVELOPMENT = "development"
    TESTING = "testing"
    HOMOLOGATION = "homologation"
    PRODUCTION = "production"


class SortOrder(BaseStrEnum):
    ASC = "asc"
    DESC = "desc"


class UserStatus(BaseStrEnum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    BLOCKED = "blocked"
    PENDING = "pending"


class RoleType(BaseStrEnum):
    ADMIN = "admin"
    SUPERVISOR = "supervisor"
    LAWYER = "advogado"
    NEGOTIATOR = "negociador"
    FINANCIAL = "financeiro"
    SUPPORT = "atendimento"
    CLIENT = "cliente"


class ClientStatus(BaseStrEnum):
    NEW = "novo"
    UNDER_ANALYSIS = "em_analise"
    NEGOTIATING = "negociando"
    AGREEMENT = "acordo"
    CLOSED = "encerrado"


class ClientType(BaseStrEnum):
    INDIVIDUAL = "pessoa_fisica"
    COMPANY = "pessoa_juridica"


class MaritalStatus(BaseStrEnum):
    SINGLE = "solteiro"
    MARRIED = "casado"
    DIVORCED = "divorciado"
    WIDOWED = "viuvo"
    STABLE_UNION = "uniao_estavel"
    SEPARATED = "separado"
    NOT_INFORMED = "nao_informado"


class Gender(BaseStrEnum):
    FEMALE = "feminino"
    MALE = "masculino"
    NON_BINARY = "nao_binario"
    OTHER = "outro"
    NOT_INFORMED = "nao_informado"


class ContactType(BaseStrEnum):
    PHONE = "telefone"
    MOBILE = "celular"
    WHATSAPP = "whatsapp"
    EMAIL = "email"
    ALTERNATIVE = "alternativo"


class AddressType(BaseStrEnum):
    RESIDENTIAL = "residencial"
    COMMERCIAL = "comercial"
    BILLING = "cobranca"
    CORRESPONDENCE = "correspondencia"
    OTHER = "outro"


class CreditorType(BaseStrEnum):
    PUBLIC = "publico"
    PRIVATE = "privado"
    INDIVIDUAL = "pessoa_fisica"


class CreditorCategory(BaseStrEnum):
    BANK = "banco"
    FINANCIAL_INSTITUTION = "financeira"
    UTILITY = "concessionaria"
    TAX_AUTHORITY = "fisco"
    CONDOMINIUM = "condominio"
    MUNICIPALITY = "municipio"
    INDIVIDUAL = "pessoa_fisica"
    OTHER = "outro"


class DebtStatus(BaseStrEnum):
    ACTIVE = "ativa"
    NEGOTIATING = "negociando"
    AGREEMENT = "acordo"
    SETTLED = "quitada"
    CANCELED = "cancelada"


class DebtType(BaseStrEnum):
    CREDIT_CARD = "cartao_credito"
    PERSONAL_LOAN = "emprestimo_pessoal"
    PAYROLL_LOAN = "consignado"
    OVERDRAFT = "cheque_especial"
    FINANCING = "financiamento"
    UTILITY_BILL = "conta_consumo"
    TAX = "tributo"
    CONDOMINIUM = "condominio"
    OTHER = "outro"


class InstallmentStatus(BaseStrEnum):
    OPEN = "aberta"
    OVERDUE = "vencida"
    PAID = "paga"
    RENEGOTIATED = "renegociada"
    CANCELED = "cancelada"


class NegotiationStatus(BaseStrEnum):
    OPEN = "em_aberto"
    ACCEPTED = "aceita"
    REJECTED = "recusada"
    EXPIRED = "expirada"
    CANCELED = "cancelada"


class ProposalStatus(BaseStrEnum):
    DRAFT = "rascunho"
    SENT = "enviada"
    ACCEPTED = "aceita"
    REJECTED = "recusada"
    EXPIRED = "expirada"
    CANCELED = "cancelada"


class DocumentStatus(BaseStrEnum):
    PENDING = "pendente"
    SENT = "enviado"
    VALIDATED = "validado"
    REJECTED = "rejeitado"
    ARCHIVED = "arquivado"


class DocumentType(BaseStrEnum):
    CPF = "cpf"
    RG = "rg"
    CNH = "cnh"
    CONTRACT = "contrato"
    BANK_STATEMENT = "extrato"
    COURT_CASE = "processo"
    RECEIPT = "comprovante"
    PAYSLIP = "holerite"
    INCOME_TAX = "imposto_renda"
    PHOTO = "foto"
    AUDIO = "audio"
    VIDEO = "video"
    OTHER = "outro"


class TaskStatus(BaseStrEnum):
    OPEN = "aberta"
    IN_PROGRESS = "em_andamento"
    COMPLETED = "concluida"
    CANCELED = "cancelada"


class TaskPriority(BaseStrEnum):
    LOW = "baixa"
    MEDIUM = "media"
    HIGH = "alta"
    URGENT = "urgente"


class WorkflowStage(BaseStrEnum):
    NEW_CLIENT = "novo_cliente"
    DOCUMENTATION = "documentacao"
    DIAGNOSIS = "diagnostico"
    LEGAL_OPINION = "parecer"
    NEGOTIATION = "negociacao"
    AGREEMENT = "acordo"
    FINISHED = "finalizado"


class AuditAction(BaseStrEnum):
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"
    RESTORE = "restore"
    LOGIN = "login"
    LOGOUT = "logout"
    CHANGE_PASSWORD = "change_password"
    RESET_PASSWORD = "reset_password"
    EXPORT = "export"
    IMPORT = "import"
    VIEW = "view"


class AuditEntityType(BaseStrEnum):
    ORGANIZATION = "organization"
    USER = "user"
    CLIENT = "client"
    CREDITOR = "creditor"
    DEBT = "debt"
    NEGOTIATION = "negotiation"
    PROPOSAL = "proposal"
    DOCUMENT = "document"
    TASK = "task"
    AUTH = "auth"
    SYSTEM = "system"


class StorageProviderType(BaseStrEnum):
    LOCAL = "local"
    S3 = "s3"
    MINIO = "minio"


class ExportFormat(BaseStrEnum):
    CSV = "csv"
    XLSX = "xlsx"
    PDF = "pdf"


class LogFormat(BaseStrEnum):
    JSON = "json"
    TEXT = "text"


class HealthStatus(BaseStrEnum):
    OK = "ok"
    DEGRADED = "degraded"
    DOWN = "down"


class NotificationChannel(BaseStrEnum):
    IN_APP = "in_app"
    EMAIL = "email"
    SMS = "sms"
    WHATSAPP = "whatsapp"


class NotificationStatus(BaseStrEnum):
    PENDING = "pending"
    SENT = "sent"
    FAILED = "failed"
    READ = "read"


class FinancialProfileStatus(BaseStrEnum):
    DRAFT = "rascunho"
    COMPLETED = "concluido"
    UNDER_REVIEW = "em_revisao"
    APPROVED = "aprovado"


class DiagnosisStatus(BaseStrEnum):
    DRAFT = "rascunho"
    PROCESSING = "processando"
    COMPLETED = "concluido"
    FAILED = "falhou"


class CurrencyCode(BaseStrEnum):
    BRL = "BRL"
    USD = "USD"
    EUR = "EUR"


class LanguageCode(BaseStrEnum):
    PT_BR = "pt-BR"
    EN_US = "en-US"
    ES_ES = "es-ES"


class EventType(BaseStrEnum):
    USER_CREATED = "user_created"
    CLIENT_CREATED = "client_created"
    DEBT_CREATED = "debt_created"
    PROPOSAL_ACCEPTED = "proposal_accepted"
    AGREEMENT_SIGNED = "agreement_signed"
    PASSWORD_CHANGED = "password_changed"


__all__ = [
    "BaseStrEnum",
    "Environment",
    "SortOrder",
    "UserStatus",
    "RoleType",
    "ClientStatus",
    "ClientType",
    "MaritalStatus",
    "Gender",
    "ContactType",
    "AddressType",
    "CreditorType",
    "CreditorCategory",
    "DebtStatus",
    "DebtType",
    "InstallmentStatus",
    "NegotiationStatus",
    "ProposalStatus",
    "DocumentStatus",
    "DocumentType",
    "TaskStatus",
    "TaskPriority",
    "WorkflowStage",
    "AuditAction",
    "AuditEntityType",
    "StorageProviderType",
    "ExportFormat",
    "LogFormat",
    "HealthStatus",
    "NotificationChannel",
    "NotificationStatus",
    "FinancialProfileStatus",
    "DiagnosisStatus",
    "CurrencyCode",
    "LanguageCode",
    "EventType",
]
