from fastapi import APIRouter, HTTPException, Response
from app.core.config import settings
from app.observability import render_openmetrics
router=APIRouter()
@router.get("/metrics", include_in_schema=False)
def metrics():
    if not settings.metrics_enabled:
        raise HTTPException(status_code=404, detail="Not Found")
    return Response(render_openmetrics(), media_type="application/openmetrics-text; version=1.0.0; charset=utf-8")
