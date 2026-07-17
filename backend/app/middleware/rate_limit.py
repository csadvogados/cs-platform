from __future__ import annotations
from collections import defaultdict, deque
from threading import Lock
import time
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from app.core.config import settings

class RateLimitMiddleware(BaseHTTPMiddleware):
    """Lightweight per-process limiter. For horizontal scaling, replace storage with Redis."""
    _events: dict[str, deque[float]] = defaultdict(deque)
    _lock = Lock()

    @staticmethod
    def _client_ip(request: Request) -> str:
        if settings.trusted_proxy_headers:
            forwarded = request.headers.get("x-forwarded-for")
            if forwarded:
                return forwarded.split(",", 1)[0].strip()
        return request.client.host if request.client else "unknown"

    async def dispatch(self, request: Request, call_next):
        if not settings.rate_limit_enabled or settings.environment == "test":
            return await call_next(request)
        path = request.url.path
        limit = settings.login_rate_limit_requests if path.endswith(("/auth/login", "/auth/token")) else settings.rate_limit_requests
        window = settings.rate_limit_window_seconds
        key = f"{self._client_ip(request)}:{path if path.endswith(('/auth/login','/auth/token')) else '*'}"
        now = time.monotonic()
        with self._lock:
            bucket = self._events[key]
            while bucket and now - bucket[0] >= window:
                bucket.popleft()
            if len(bucket) >= limit:
                retry_after = max(1, int(window - (now - bucket[0])))
                return JSONResponse(
                    status_code=429,
                    content={"success": False, "error": {"code": "RATE_LIMITED", "message": "Muitas requisições. Tente novamente em instantes."}},
                    headers={"Retry-After": str(retry_after)},
                )
            bucket.append(now)
        response = await call_next(request)
        response.headers.setdefault("X-RateLimit-Limit", str(limit))
        return response

__all__ = ["RateLimitMiddleware"]
