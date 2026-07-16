from __future__ import annotations

import time
from uuid import uuid4

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

from app.core.constants import (
    CORRELATION_ID_HEADER,
    REQUEST_ID_HEADER,
)


class RequestContextMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        request_id = (
            request.headers.get(REQUEST_ID_HEADER)
            or str(uuid4())
        )
        correlation_id = (
            request.headers.get(CORRELATION_ID_HEADER)
            or request_id
        )

        request.state.request_id = request_id
        request.state.correlation_id = correlation_id

        started_at = time.perf_counter()

        response = await call_next(request)

        duration_ms = round(
            (time.perf_counter() - started_at) * 1000,
            2,
        )

        response.headers[REQUEST_ID_HEADER] = request_id
        response.headers[CORRELATION_ID_HEADER] = correlation_id
        response.headers["X-Response-Time-Ms"] = str(duration_ms)

        return response


__all__ = ["RequestContextMiddleware"]
