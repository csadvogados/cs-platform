from contextlib import asynccontextmanager
import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.docs import (
    get_swagger_ui_html,
    get_swagger_ui_oauth2_redirect_html,
)
from fastapi.staticfiles import StaticFiles
from swagger_ui_bundle import swagger_ui_path

from app.api.exception_handlers import register_exception_handlers
from app.api.routes import (
    auth,
    audit,
    clients,
    dashboard,
    diagnoses,
    financial,
    performance,
    payment_plans,
    recovery_cases,
    notifications,
    health,
    metrics,
    crm,
    organizations,
    users,
    access_control,
)
from app.core.config import settings
from app.core.logging import configure_logging
from app.db.session import SessionLocal
from app.middleware import (
    RequestContextMiddleware,
    SecurityHeadersMiddleware,
    RateLimitMiddleware,
)
from app.observability import MetricsMiddleware
from app.services.bootstrap import bootstrap
from app.startup.database_initializer import initialize_database

from app.models import *  # noqa: F401,F403
from app.models.organization_registry import *  # noqa: F401,F403


configure_logging()
logger = logging.getLogger("cs_platform.startup")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(
        "Iniciando %s versao %s no ambiente %s.",
        settings.app_name,
        settings.app_version,
        settings.environment,
    )

    initialize_database()

    with SessionLocal() as db:
        bootstrap(db)

    logger.info("Inicializacao concluida com sucesso.")
    yield
    logger.info("Encerrando aplicacao.")


app = FastAPI(
    title="CS Platform API",
    version=settings.app_version,
    description=(
        "CS Platform Enterprise: identidade, organizacoes, usuarios, CRM, "
        "gestao financeira, diagnostico e observabilidade."
    ),
    lifespan=lifespan,
    docs_url=None,
    redoc_url=settings.redoc_url,
    openapi_url=settings.openapi_url,
)

app.mount(
    "/swagger-static",
    StaticFiles(directory=swagger_ui_path),
    name="swagger-static",
)


@app.get(settings.docs_url, include_in_schema=False)
def local_swagger_ui():
    return get_swagger_ui_html(
        openapi_url=settings.openapi_url,
        title=f"{app.title} - Swagger UI",
        oauth2_redirect_url=app.swagger_ui_oauth2_redirect_url,
        swagger_js_url="/swagger-static/swagger-ui-bundle.js",
        swagger_css_url="/swagger-static/swagger-ui.css",
        swagger_favicon_url="/swagger-static/favicon-32x32.png",
    )


@app.get(app.swagger_ui_oauth2_redirect_url, include_in_schema=False)
def swagger_ui_redirect():
    return get_swagger_ui_oauth2_redirect_html()


register_exception_handlers(app)

app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(RateLimitMiddleware)
app.add_middleware(MetricsMiddleware)
app.add_middleware(RequestContextMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(metrics.router)
app.include_router(
    health.router,
    prefix=settings.api_v1_prefix,
    tags=["Health"],
)
app.include_router(
    auth.router,
    prefix=f"{settings.api_v1_prefix}/auth",
    tags=["Authentication"],
)
app.include_router(
    users.router,
    prefix=f"{settings.api_v1_prefix}/users",
    tags=["Users"],
)
app.include_router(
    audit.router,
    prefix=f"{settings.api_v1_prefix}/audit",
    tags=["Audit"],
)

app.include_router(
    access_control.roles_router,
    prefix=f"{settings.api_v1_prefix}/roles",
    tags=["Roles"],
)
app.include_router(
    access_control.permissions_router,
    prefix=f"{settings.api_v1_prefix}/permissions",
    tags=["Permissions"],
)
app.include_router(
    access_control.invitations_router,
    prefix=f"{settings.api_v1_prefix}/invitations",
    tags=["Invitations"],
)
app.include_router(
    access_control.sessions_router,
    prefix=f"{settings.api_v1_prefix}/sessions",
    tags=["Sessions"],
)

if settings.organization_api_enabled:
    app.include_router(
        organizations.router,
        prefix=f"{settings.api_v1_prefix}/organizations",
        tags=["Organizations"],
    )
app.include_router(
    crm.router,
    prefix=f"{settings.api_v1_prefix}/crm",
    tags=["CRM Enterprise"],
)
app.include_router(
    clients.router,
    prefix=f"{settings.api_v1_prefix}/clients",
    tags=["Clients"],
)
app.include_router(
    financial.router,
    prefix=f"{settings.api_v1_prefix}/financial",
    tags=["Financial and Debts"],
)
app.include_router(
    performance.router,
    prefix=f"{settings.api_v1_prefix}/performance",
    tags=["Performance goals"],
)
app.include_router(
    notifications.router,
    prefix=f"{settings.api_v1_prefix}/notifications",
    tags=["Notifications"],
)
app.include_router(
    diagnoses.router,
    prefix=f"{settings.api_v1_prefix}/diagnoses",
    tags=["Diagnoses"],
)
app.include_router(
    payment_plans.router,
    prefix=f"{settings.api_v1_prefix}/payment-plans",
    tags=["Payment Plan Engine"],
)
app.include_router(
    recovery_cases.router,
    prefix=f"{settings.api_v1_prefix}/recovery-cases",
    tags=["Recovery Cases"],
)
app.include_router(
    dashboard.router,
    prefix=f"{settings.api_v1_prefix}/dashboard",
    tags=["Dashboard"],
)


@app.get("/", tags=["Root"])
def root():
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "environment": settings.environment,
        "swagger": settings.docs_url,
        "health": f"{settings.api_v1_prefix}/health",
    }


@app.get("/ping", tags=["Root"])
def ping():
    return {
        "status": "ok",
        "version": settings.app_version,
    }
