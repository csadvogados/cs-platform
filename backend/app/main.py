from contextlib import asynccontextmanager
import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.exception_handlers import register_exception_handlers
from app.api.routes import (
    auth,
    clients,
    dashboard,
    diagnoses,
    financial,
    health,
    organizations,
    users,
)
from app.core.config import settings
from app.core.logging import configure_logging
from app.db.session import SessionLocal
from app.middleware import (
    RequestContextMiddleware,
    SecurityHeadersMiddleware,
)
from app.services.bootstrap import bootstrap
from app.startup.database_initializer import initialize_database

from app.models import *  # noqa: F401,F403
from app.models.organization_registry import *  # noqa: F401,F403


configure_logging()
logger = logging.getLogger("cs_platform.startup")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(
        "Iniciando %s versão %s no ambiente %s.",
        settings.app_name,
        settings.app_version,
        settings.environment,
    )

    initialize_database()

    with SessionLocal() as db:
        bootstrap(db)

    logger.info("Inicialização concluída com sucesso.")
    yield
    logger.info("Encerrando aplicação.")


app = FastAPI(
    title="CS Platform API",
    version=settings.app_version,
    description=(
        "CS Platform: autenticação, clientes, cadastro financeiro, "
        "dívidas, diagnóstico e parecer econômico."
    ),
    lifespan=lifespan,
    docs_url=settings.docs_url,
    redoc_url=settings.redoc_url,
    openapi_url=settings.openapi_url,
)

register_exception_handlers(app)

app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(RequestContextMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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
if settings.organization_api_enabled:
    app.include_router(
        organizations.router,
        prefix=f"{settings.api_v1_prefix}/organizations",
        tags=["Organizations"],
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
    diagnoses.router,
    prefix=f"{settings.api_v1_prefix}/diagnoses",
    tags=["Diagnoses"],
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
