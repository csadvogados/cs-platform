from __future__ import annotations

from contextvars import ContextVar
from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True, slots=True)
class SecurityContext:
    user_id: UUID | None = None
    organization_id: UUID | None = None
    role: str | None = None
    request_id: str | None = None
    correlation_id: str | None = None


_security_context: ContextVar[SecurityContext] = ContextVar(
    "cs_platform_security_context",
    default=SecurityContext(),
)


def get_security_context() -> SecurityContext:
    return _security_context.get()


def set_security_context(
    context: SecurityContext,
):
    return _security_context.set(context)


def reset_security_context(token) -> None:
    _security_context.reset(token)


__all__ = [
    "SecurityContext",
    "get_security_context",
    "set_security_context",
    "reset_security_context",
]
