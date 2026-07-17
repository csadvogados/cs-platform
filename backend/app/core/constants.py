"""
CS Platform Enterprise
Release v5.0.0 - TITANIUM
Pacote 01A - Foundation Core
Entrega 01A.2

Arquivo:
    backend/app/core/constants.py

Finalidade:
    Centralizar constantes compartilhadas da aplicação, evitando valores
    literais espalhados pelo código e facilitando manutenção, testes e
    configuração por ambiente.
"""

from __future__ import annotations

from typing import Final


# ==========================================================
# IDENTIDADE DA APLICAÇÃO
# ==========================================================

APP_NAME: Final[str] = "CS Platform"
APP_TITLE: Final[str] = "CS Platform Enterprise"
APP_VERSION: Final[str] = "5.3.0"
APP_RELEASE_NAME: Final[str] = "TITANIUM"
DEFAULT_ENVIRONMENT: Final[str] = "development"


# ==========================================================
# API
# ==========================================================

API_V1_PREFIX: Final[str] = "/api/v1"
OPENAPI_URL: Final[str] = "/openapi.json"
DOCS_URL: Final[str] = "/docs"
REDOC_URL: Final[str] = "/redoc"

DEFAULT_RESPONSE_MEDIA_TYPE: Final[str] = "application/json"
CORRELATION_ID_HEADER: Final[str] = "X-Correlation-ID"
REQUEST_ID_HEADER: Final[str] = "X-Request-ID"
IDEMPOTENCY_KEY_HEADER: Final[str] = "Idempotency-Key"
ORGANIZATION_ID_HEADER: Final[str] = "X-Organization-ID"


# ==========================================================
# PAGINAÇÃO E ORDENAÇÃO
# ==========================================================

DEFAULT_PAGE: Final[int] = 1
DEFAULT_PAGE_SIZE: Final[int] = 25
MIN_PAGE_SIZE: Final[int] = 1
MAX_PAGE_SIZE: Final[int] = 100
DEFAULT_SORT_ORDER: Final[str] = "asc"
ALLOWED_SORT_ORDERS: Final[tuple[str, str]] = ("asc", "desc")


# ==========================================================
# AUTENTICAÇÃO E SESSÃO
# ==========================================================

JWT_ALGORITHM: Final[str] = "HS256"
DEFAULT_ACCESS_TOKEN_EXPIRE_MINUTES: Final[int] = 30
DEFAULT_REFRESH_TOKEN_EXPIRE_DAYS: Final[int] = 7
DEFAULT_LOGIN_LOCK_MINUTES: Final[int] = 15
DEFAULT_MAX_FAILED_LOGIN_ATTEMPTS: Final[int] = 5

ACCESS_TOKEN_TYPE: Final[str] = "access"
REFRESH_TOKEN_TYPE: Final[str] = "refresh"
BEARER_TOKEN_TYPE: Final[str] = "bearer"

PASSWORD_MIN_LENGTH: Final[int] = 12
PASSWORD_MAX_LENGTH: Final[int] = 128


# ==========================================================
# USUÁRIOS E PERFIS
# ==========================================================

ROLE_ADMIN: Final[str] = "admin"
ROLE_SUPERVISOR: Final[str] = "supervisor"
ROLE_LAWYER: Final[str] = "advogado"
ROLE_NEGOTIATOR: Final[str] = "negociador"
ROLE_FINANCIAL: Final[str] = "financeiro"
ROLE_SUPPORT: Final[str] = "atendimento"
ROLE_CLIENT: Final[str] = "cliente"

SYSTEM_ROLES: Final[tuple[str, ...]] = (
    ROLE_ADMIN,
    ROLE_SUPERVISOR,
    ROLE_LAWYER,
    ROLE_NEGOTIATOR,
    ROLE_FINANCIAL,
    ROLE_SUPPORT,
    ROLE_CLIENT,
)

USER_STATUS_ACTIVE: Final[str] = "active"
USER_STATUS_INACTIVE: Final[str] = "inactive"
USER_STATUS_BLOCKED: Final[str] = "blocked"
USER_STATUS_PENDING: Final[str] = "pending"

USER_STATUSES: Final[tuple[str, ...]] = (
    USER_STATUS_ACTIVE,
    USER_STATUS_INACTIVE,
    USER_STATUS_BLOCKED,
    USER_STATUS_PENDING,
)


# ==========================================================
# MULTI-TENANCY
# ==========================================================

DEFAULT_ORGANIZATION_NAME: Final[str] = "CS Advogados"
DEFAULT_TRADE_NAME: Final[str] = "CS Recupera"


# ==========================================================
# AUDITORIA
# ==========================================================

AUDIT_ACTION_CREATE: Final[str] = "create"
AUDIT_ACTION_UPDATE: Final[str] = "update"
AUDIT_ACTION_DELETE: Final[str] = "delete"
AUDIT_ACTION_RESTORE: Final[str] = "restore"
AUDIT_ACTION_LOGIN: Final[str] = "login"
AUDIT_ACTION_LOGOUT: Final[str] = "logout"
AUDIT_ACTION_PASSWORD_CHANGE: Final[str] = "change_password"

AUDIT_ACTIONS: Final[tuple[str, ...]] = (
    AUDIT_ACTION_CREATE,
    AUDIT_ACTION_UPDATE,
    AUDIT_ACTION_DELETE,
    AUDIT_ACTION_RESTORE,
    AUDIT_ACTION_LOGIN,
    AUDIT_ACTION_LOGOUT,
    AUDIT_ACTION_PASSWORD_CHANGE,
)


# ==========================================================
# STORAGE E UPLOADS
# ==========================================================

STORAGE_PROVIDER_LOCAL: Final[str] = "local"
STORAGE_PROVIDER_S3: Final[str] = "s3"
STORAGE_PROVIDER_MINIO: Final[str] = "minio"

DEFAULT_STORAGE_PROVIDER: Final[str] = STORAGE_PROVIDER_LOCAL
DEFAULT_UPLOAD_DIRECTORY: Final[str] = "uploads"

MAX_UPLOAD_SIZE_MB: Final[int] = 25
MAX_UPLOAD_SIZE_BYTES: Final[int] = MAX_UPLOAD_SIZE_MB * 1024 * 1024

ALLOWED_DOCUMENT_EXTENSIONS: Final[tuple[str, ...]] = (
    ".pdf",
    ".doc",
    ".docx",
    ".xls",
    ".xlsx",
    ".csv",
    ".txt",
    ".jpg",
    ".jpeg",
    ".png",
    ".webp",
)

ALLOWED_DOCUMENT_MIME_TYPES: Final[tuple[str, ...]] = (
    "application/pdf",
    "application/msword",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/vnd.ms-excel",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "text/csv",
    "text/plain",
    "image/jpeg",
    "image/png",
    "image/webp",
)


# ==========================================================
# LOCALIZAÇÃO
# ==========================================================

DEFAULT_LANGUAGE: Final[str] = "pt-BR"
DEFAULT_TIMEZONE: Final[str] = "America/Sao_Paulo"
DEFAULT_CURRENCY: Final[str] = "BRL"
DEFAULT_COUNTRY_CODE: Final[str] = "BR"


# ==========================================================
# FORMATOS
# ==========================================================

DATE_FORMAT: Final[str] = "%Y-%m-%d"
DATETIME_FORMAT: Final[str] = "%Y-%m-%dT%H:%M:%S%z"
DISPLAY_DATE_FORMAT: Final[str] = "%d/%m/%Y"
DISPLAY_DATETIME_FORMAT: Final[str] = "%d/%m/%Y %H:%M"


# ==========================================================
# HTTP E ERROS
# ==========================================================

ERROR_CODE_VALIDATION: Final[str] = "VALIDATION_ERROR"
ERROR_CODE_AUTHENTICATION: Final[str] = "AUTHENTICATION_ERROR"
ERROR_CODE_PERMISSION_DENIED: Final[str] = "PERMISSION_DENIED"
ERROR_CODE_NOT_FOUND: Final[str] = "RESOURCE_NOT_FOUND"
ERROR_CODE_CONFLICT: Final[str] = "RESOURCE_CONFLICT"
ERROR_CODE_INTERNAL: Final[str] = "INTERNAL_SERVER_ERROR"


# ==========================================================
# HEALTHCHECK
# ==========================================================

HEALTH_STATUS_OK: Final[str] = "ok"
HEALTH_STATUS_DEGRADED: Final[str] = "degraded"
HEALTH_STATUS_DOWN: Final[str] = "down"


# ==========================================================
# CACHE E TEMPOS
# ==========================================================

DEFAULT_CACHE_TTL_SECONDS: Final[int] = 300
SHORT_CACHE_TTL_SECONDS: Final[int] = 60
LONG_CACHE_TTL_SECONDS: Final[int] = 3600


# ==========================================================
# BANCO DE DADOS
# ==========================================================

DEFAULT_DATABASE_POOL_SIZE: Final[int] = 5
DEFAULT_DATABASE_MAX_OVERFLOW: Final[int] = 10
DEFAULT_DATABASE_POOL_TIMEOUT_SECONDS: Final[int] = 30
DEFAULT_DATABASE_POOL_RECYCLE_SECONDS: Final[int] = 1800


# ==========================================================
# LOGS
# ==========================================================

DEFAULT_LOG_LEVEL: Final[str] = "INFO"
LOG_FORMAT_JSON: Final[str] = "json"
LOG_FORMAT_TEXT: Final[str] = "text"


# ==========================================================
# EXPORTAÇÕES
# ==========================================================

EXPORT_FORMAT_CSV: Final[str] = "csv"
EXPORT_FORMAT_XLSX: Final[str] = "xlsx"
EXPORT_FORMAT_PDF: Final[str] = "pdf"

SUPPORTED_EXPORT_FORMATS: Final[tuple[str, ...]] = (
    EXPORT_FORMAT_CSV,
    EXPORT_FORMAT_XLSX,
    EXPORT_FORMAT_PDF,
)


__all__ = [
    name
    for name in globals()
    if name.isupper() and not name.startswith("_")
]
