import secrets

from fastapi import APIRouter, Header, HTTPException, Response
from app.core.config import settings
from app.observability import render_openmetrics
router=APIRouter()
@router.get("/metrics", include_in_schema=False)
def metrics(authorization: str | None = Header(default=None)):
    if not settings.metrics_enabled:
        raise HTTPException(status_code=404, detail="Not Found")
    if settings.is_production:
        expected = settings.metrics_token.strip()
        supplied = ""
        if authorization and authorization.lower().startswith("bearer "):
            supplied = authorization[7:].strip()
        if not expected or not secrets.compare_digest(supplied, expected):
            raise HTTPException(status_code=404, detail="Not Found")
    return Response(render_openmetrics(), media_type="application/openmetrics-text; version=1.0.0; charset=utf-8")
