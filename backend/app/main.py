from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.db.base import Base
from app.db.session import SessionLocal, engine
from app.models import *  # noqa
from app.services.bootstrap import bootstrap
from app.api.routes import auth, clients, health, users, financial, diagnoses, dashboard

@asynccontextmanager
async def lifespan(app: FastAPI):
    if settings.environment in {"development","test"}:
        Base.metadata.create_all(bind=engine)
    with SessionLocal() as db:
        bootstrap(db)
    yield

app = FastAPI(title="CS Platform API", version=settings.app_version, description="Sprints 1 e 2 integradas: autenticação, clientes, cadastro financeiro, dívidas, diagnóstico e parecer econômico.", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=settings.cors_origin_list, allow_credentials=True, allow_methods=["*"], allow_headers=["*"])
app.include_router(health.router, prefix="/api/v1", tags=["Health"])
app.include_router(auth.router, prefix="/api/v1/auth", tags=["Authentication"])
app.include_router(users.router, prefix="/api/v1/users", tags=["Users"])
app.include_router(clients.router, prefix="/api/v1/clients", tags=["Clients"])
app.include_router(financial.router, prefix="/api/v1/financial", tags=["Financial and Debts"])
app.include_router(diagnoses.router, prefix="/api/v1/diagnoses", tags=["Diagnoses"])
app.include_router(dashboard.router, prefix="/api/v1/dashboard", tags=["Dashboard"])

@app.get("/")
def root():
    return {"name": settings.app_name, "version": settings.app_version, "swagger": "/docs", "health": "/api/v1/health"}
