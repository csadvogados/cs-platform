from __future__ import annotations

from typing import Any, Generic, TypeVar

from pydantic import BaseModel, ConfigDict, Field


T = TypeVar("T")


class ErrorBody(BaseModel):
    model_config = ConfigDict(extra="allow")

    code: str
    message: str
    details: dict[str, Any] | None = None


class SuccessResponse(BaseModel, Generic[T]):
    success: bool = True
    data: T
    meta: dict[str, Any] = Field(default_factory=dict)


class ErrorResponse(BaseModel):
    success: bool = False
    error: ErrorBody


def success_response(
    data: T,
    *,
    meta: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return SuccessResponse[T](
        data=data,
        meta=meta or {},
    ).model_dump()


def error_response(
    code: str,
    message: str,
    *,
    details: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return ErrorResponse(
        error=ErrorBody(
            code=code,
            message=message,
            details=details,
        )
    ).model_dump(exclude_none=True)


__all__ = [
    "ErrorBody",
    "SuccessResponse",
    "ErrorResponse",
    "success_response",
    "error_response",
]
