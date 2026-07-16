from contextlib import asynccontextmanager
import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import (
    auth,
    clients,
    dashboard,
    diagnoses,
    financial,
    health,
    users,
)
from app.core.config import settings
from app.db.session import SessionLocal
from app.services.bootstrap import bootstrap
from app.startup.database_initializer import initialize_database

# Garante que todos os modelos sejam registrados no metadata do SQLAlchemy.
from app.models import *  # noqa: F401,F403


logger = logging.getLogger("cs_platform.startup")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Ciclo de vida da aplicação.

    Ordem de inicialização:
    1. valida a conexão com o banco;
    2. confirma a estrutura existente;
    3. executa o bootstrap da organização e do administrador;
    4. libera a aplicação para receber requisições.
    """
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
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(
    health.router,
    prefix="/api/v1",
    tags=["Health"],
)

app.include_router(
    auth.router,
    prefix="/api/v1/auth",
    tags=["Authentication"],
)

app.include_router(
    users.router,
    prefix="/api/v1/users",
    tags=["Users"],
)

app.include_router(
    clients.router,
    prefix="/api/v1/clients",
    tags=["Clients"],
)

app.include_router(
    financial.router,
    prefix="/api/v1/financial",
    tags=["Financial and Debts"],
)

app.include_router(
    diagnoses.router,
    prefix="/api/v1/diagnoses",
    tags=["Diagnoses"],
)

app.include_router(
    dashboard.router,
    prefix="/api/v1/dashboard",
    tags=["Dashboard"],
)


@app.get(
    "/",
    tags=["Root"],
)
def root():
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "environment": settings.environment,
        "swagger": "/docs",
        "health": "/api/v1/health",
    }


@app.get(
    "/ping",
    tags=["Root"],
)
def ping():
    return {
        "status": "ok",
    }
