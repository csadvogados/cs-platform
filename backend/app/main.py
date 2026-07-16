from contextlib import asynccontextmanager
import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import admin_recovery, auth, clients, dashboard, diagnoses, financial, health, users
from app.core.config import settings
from app.db.session import SessionLocal
from app.services.bootstrap import bootstrap
from app.startup.database_initializer import initialize_database

from app.models import *  # noqa: F401,F403

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
        "CS Platform: autenticação, clientes, cadastro financeiro, dívidas, "
        "diagnóstico e parecer econômico."
    ),
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],

app.include_router(admin_recovery.router,prefix="/api/v1/admin-recovery",tags=["Temporary Admin Recovery"],

app.include_router(health.router, prefix="/api/v1", tags=["Health"])
app.include_router(auth.router, prefix="/api/v1/auth", tags=["Authentication"])
app.include_router(users.router, prefix="/api/v1/users", tags=["Users"])
app.include_router(clients.router, prefix="/api/v1/clients", tags=["Clients"])
app.include_router(financial.router, prefix="/api/v1/financial", tags=["Financial and Debts"])
app.include_router(diagnoses.router, prefix="/api/v1/diagnoses", tags=["Diagnoses"])
app.include_router(dashboard.router, prefix="/api/v1/dashboard", tags=["Dashboard"])


@app.get("/")
def root():
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "environment": settings.environment,
        "swagger": "/docs",
        "health": "/api/v1/health",
    }
