from __future__ import annotations
from collections import Counter
from threading import Lock
import time
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

_lock = Lock()
_requests = Counter()
_duration_sum = Counter()

class MetricsMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        started = time.perf_counter()
        response = await call_next(request)
        elapsed = time.perf_counter() - started
        key = (request.method, request.url.path, response.status_code)
        with _lock:
            _requests[key] += 1
            _duration_sum[key] += elapsed
        return response

def render_openmetrics() -> str:
    lines = [
        "# HELP cs_platform_http_requests_total Total de requisições HTTP.",
        "# TYPE cs_platform_http_requests_total counter",
    ]
    with _lock:
        items = list(_requests.items())
        durations = dict(_duration_sum)
    for (method, path, status), count in sorted(items, key=str):
        labels=f'method="{method}",path="{path}",status="{status}"'
        lines.append(f"cs_platform_http_requests_total{{{labels}}} {count}")
    lines += ["# HELP cs_platform_http_request_duration_seconds_sum Soma da duração HTTP.", "# TYPE cs_platform_http_request_duration_seconds_sum counter"]
    for (method, path, status), _ in sorted(items, key=str):
        labels=f'method="{method}",path="{path}",status="{status}"'
        lines.append(f"cs_platform_http_request_duration_seconds_sum{{{labels}}} {durations[(method,path,status)]:.6f}")
    return "\n".join(lines) + "\n"
