from __future__ import annotations

import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.exceptions import (
    ApplicationException,
    AuthenticationException,
    AuthorizationException,
    ConflictException,
    LockedResourceException,
    RateLimitException,
    ResourceNotFoundException,
    ValidationException,
)
from app.core.responses import error_response


logger = logging.getLogger("cs_platform.exceptions")


def _application_status_code(exc: ApplicationException) -> int:
    if isinstance(exc, AuthenticationException):
        return 401
    if isinstance(exc, AuthorizationException):
        return 403
    if isinstance(exc, ResourceNotFoundException):
        return 404
    if isinstance(exc, LockedResourceException):
        return 423
    if isinstance(exc, RateLimitException):
        return 429
    if isinstance(exc, ConflictException):
        return 409
    if isinstance(exc, ValidationException):
        return 422
    return 400


async def application_exception_handler(
    request: Request,
    exc: ApplicationException,
) -> JSONResponse:
    status_code = _application_status_code(exc)

    logger.warning(
        "Erro controlado na aplicação.",
        extra={
            "error_code": exc.code,
            "path": request.url.path,
            "method": request.method,
            "status_code": status_code,
        },
    )

    return JSONResponse(
        status_code=status_code,
        content=error_response(
            exc.code,
            exc.message,
            details=exc.details or None,
        ),
    )


async def validation_exception_handler(
    request: Request,
    exc: RequestValidationError,
) -> JSONResponse:
    return JSONResponse(
        status_code=422,
        content=error_response(
            "REQUEST_VALIDATION_ERROR",
            "Os dados enviados são inválidos.",
            details={"errors": exc.errors()},
        ),
    )


async def http_exception_handler(
    request: Request,
    exc: StarletteHTTPException,
) -> JSONResponse:
    message = (
        exc.detail
        if isinstance(exc.detail, str)
        else "A requisição não pôde ser processada."
    )

    return JSONResponse(
        status_code=exc.status_code,
        content=error_response(
            f"HTTP_{exc.status_code}",
            message,
        ),
        headers=exc.headers,
    )


async def integrity_exception_handler(
    request: Request,
    exc: IntegrityError,
) -> JSONResponse:
    logger.exception(
        "Violação de integridade.",
        extra={
            "path": request.url.path,
            "method": request.method,
        },
    )

    return JSONResponse(
        status_code=409,
        content=error_response(
            "DATABASE_INTEGRITY_ERROR",
            "A operação viola uma regra de integridade.",
        ),
    )


async def database_exception_handler(
    request: Request,
    exc: SQLAlchemyError,
) -> JSONResponse:
    logger.exception(
        "Erro de banco de dados.",
        extra={
            "path": request.url.path,
            "method": request.method,
        },
    )

    return JSONResponse(
        status_code=500,
        content=error_response(
            "DATABASE_ERROR",
            "Não foi possível concluir a operação.",
        ),
    )


async def unhandled_exception_handler(
    request: Request,
    exc: Exception,
) -> JSONResponse:
    logger.exception(
        "Erro não tratado.",
        extra={
            "path": request.url.path,
            "method": request.method,
        },
    )

    return JSONResponse(
        status_code=500,
        content=error_response(
            "INTERNAL_SERVER_ERROR",
            "Ocorreu um erro interno.",
        ),
    )


def register_exception_handlers(app: FastAPI) -> None:
    app.add_exception_handler(
        ApplicationException,
        application_exception_handler,
    )
    app.add_exception_handler(
        RequestValidationError,
        validation_exception_handler,
    )
    app.add_exception_handler(
        StarletteHTTPException,
        http_exception_handler,
    )
    app.add_exception_handler(
        IntegrityError,
        integrity_exception_handler,
    )
    app.add_exception_handler(
        SQLAlchemyError,
        database_exception_handler,
    )
    app.add_exception_handler(
        Exception,
        unhandled_exception_handler,
    )


__all__ = ["register_exception_handlers"]
