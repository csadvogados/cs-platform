from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class ErrorContext:
    details: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any] | None) -> "ErrorContext":
        return cls(details=dict(value or {}))


class ApplicationException(Exception):
    default_code = "APPLICATION_ERROR"
    default_message = "Ocorreu um erro na aplicação."

    def __init__(
        self,
        message: str | None = None,
        *,
        code: str | None = None,
        details: Mapping[str, Any] | None = None,
        cause: Exception | None = None,
    ) -> None:
        self.code = code or self.default_code
        self.message = message or self.default_message
        self.context = ErrorContext.from_mapping(details)
        self.cause = cause
        super().__init__(self.message)

    @property
    def details(self) -> dict[str, Any]:
        return self.context.details

    def to_dict(self) -> dict[str, Any]:
        payload = {"code": self.code, "message": self.message}
        if self.details:
            payload["details"] = self.details
        return payload


class BusinessRuleException(ApplicationException):
    default_code = "BUSINESS_RULE_VIOLATION"
    default_message = "A operação viola uma regra de negócio."


class ValidationException(ApplicationException):
    default_code = "VALIDATION_ERROR"
    default_message = "Os dados informados são inválidos."


class AuthenticationException(ApplicationException):
    default_code = "AUTHENTICATION_ERROR"
    default_message = "Não foi possível autenticar o usuário."


class InvalidCredentialsException(AuthenticationException):
    default_code = "INVALID_CREDENTIALS"
    default_message = "E-mail ou senha inválidos."


class TokenException(AuthenticationException):
    default_code = "TOKEN_ERROR"
    default_message = "O token informado é inválido."


class TokenExpiredException(TokenException):
    default_code = "TOKEN_EXPIRED"
    default_message = "O token expirou."


class TokenRevokedException(TokenException):
    default_code = "TOKEN_REVOKED"
    default_message = "O token foi revogado."


class AuthorizationException(ApplicationException):
    default_code = "PERMISSION_DENIED"
    default_message = "Você não possui permissão para executar esta operação."


class TenantAccessDeniedException(AuthorizationException):
    default_code = "TENANT_ACCESS_DENIED"
    default_message = "Acesso negado aos dados desta organização."


class ResourceNotFoundException(ApplicationException):
    default_code = "RESOURCE_NOT_FOUND"
    default_message = "O recurso solicitado não foi encontrado."

    def __init__(
        self,
        resource: str | None = None,
        resource_id: Any | None = None,
        message: str | None = None,
        **kwargs: Any,
    ) -> None:
        details = dict(kwargs.pop("details", {}) or {})
        if resource is not None:
            details.setdefault("resource", resource)
        if resource_id is not None:
            details.setdefault("resource_id", str(resource_id))
        if message is None and resource:
            message = f"{resource} não encontrado."
        super().__init__(message=message, details=details, **kwargs)


class ConflictException(ApplicationException):
    default_code = "RESOURCE_CONFLICT"
    default_message = "A operação entrou em conflito com o estado atual."


class DuplicateResourceException(ConflictException):
    default_code = "DUPLICATE_RESOURCE"
    default_message = "Já existe um recurso com os dados informados."


class ConcurrencyException(ConflictException):
    default_code = "CONCURRENT_UPDATE"
    default_message = (
        "O registro foi alterado por outro usuário. "
        "Atualize os dados e tente novamente."
    )


class LockedResourceException(ConflictException):
    default_code = "RESOURCE_LOCKED"
    default_message = "O recurso está temporariamente bloqueado."


class RateLimitException(ApplicationException):
    default_code = "RATE_LIMIT_EXCEEDED"
    default_message = "Muitas tentativas. Aguarde e tente novamente."


class ExternalServiceException(ApplicationException):
    default_code = "EXTERNAL_SERVICE_ERROR"
    default_message = "O serviço externo está indisponível no momento."


class StorageException(ApplicationException):
    default_code = "STORAGE_ERROR"
    default_message = "Não foi possível processar o arquivo."


class FileValidationException(ValidationException):
    default_code = "FILE_VALIDATION_ERROR"
    default_message = "O arquivo informado é inválido."


class ConfigurationException(ApplicationException):
    default_code = "CONFIGURATION_ERROR"
    default_message = "A aplicação possui uma configuração inválida."


class DatabaseException(ApplicationException):
    default_code = "DATABASE_ERROR"
    default_message = "Não foi possível concluir a operação no banco de dados."


class InfrastructureException(ApplicationException):
    default_code = "INFRASTRUCTURE_ERROR"
    default_message = "Ocorreu uma falha de infraestrutura."


class UnsupportedOperationException(ApplicationException):
    default_code = "UNSUPPORTED_OPERATION"
    default_message = "Esta operação não é suportada."
