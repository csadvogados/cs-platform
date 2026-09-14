from __future__ import annotations

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request


API_DOC_PATHS = {"/docs", "/redoc", "/openapi.json"}

DEFAULT_CONTENT_SECURITY_POLICY = (
    "default-src 'none'; "
    "frame-ancestors 'none'; "
    "base-uri 'none'"
)

API_DOCS_CONTENT_SECURITY_POLICY = (
    "default-src 'none'; "
    "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
    "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
    "img-src 'self' data: https://fastapi.tiangolo.com; "
    "font-src 'self' data: https://cdn.jsdelivr.net; "
    "connect-src 'self'; "
    "frame-ancestors 'none'; "
    "base-uri 'none'"
)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)

        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("X-Frame-Options", "DENY")
        response.headers.setdefault(
            "Referrer-Policy",
            "strict-origin-when-cross-origin",
        )
        response.headers.setdefault(
            "Permissions-Policy",
            "camera=(), microphone=(), geolocation=()",
        )
        response.headers.setdefault("Cross-Origin-Opener-Policy", "same-origin")
        response.headers.setdefault("Cross-Origin-Resource-Policy", "same-site")

        content_security_policy = (
            API_DOCS_CONTENT_SECURITY_POLICY
            if request.url.path in API_DOC_PATHS
            else DEFAULT_CONTENT_SECURITY_POLICY
        )
        response.headers.setdefault(
            "Content-Security-Policy",
            content_security_policy,
        )

        if (
            request.url.scheme == "https"
            or request.headers.get("x-forwarded-proto") == "https"
        ):
            response.headers.setdefault(
                "Strict-Transport-Security",
                "max-age=31536000; includeSubDomains",
            )

        return response


__all__ = ["SecurityHeadersMiddleware"]
