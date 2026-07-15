import re

from sqlalchemy import create_engine
from sqlalchemy.engine import URL, make_url
from sqlalchemy.orm import sessionmaker

from app.core.config import settings


def normalize_database_url(raw_url: str) -> str:
    """
    Normaliza a URL do banco recebida de plataformas de hospedagem.

    - Remove espaços e aspas externas acidentais.
    - Converte postgresql:// para postgresql+psycopg://.
    - Corrige placeholders não resolvidos anexados ao nome do banco,
      como railway${RAILWAY}.
    - Falha com mensagem clara quando a URL está vazia ou inválida.
    """
    if not raw_url or not raw_url.strip():
        raise RuntimeError(
            "DATABASE_URL não foi definida. Configure a variável no serviço da aplicação."
        )

    cleaned = raw_url.strip().strip('"').strip("'")

    if cleaned.startswith("postgres://"):
        cleaned = cleaned.replace("postgres://", "postgresql://", 1)

    if cleaned.startswith("postgresql://"):
        cleaned = cleaned.replace(
            "postgresql://",
            "postgresql+psycopg://",
            1,
        )

    if cleaned.startswith("sqlite"):
        return cleaned

    try:
        parsed = make_url(cleaned)
    except Exception as exc:
        raise RuntimeError(
            "DATABASE_URL inválida. Use uma URL PostgreSQL completa, sem aspas "
            "e sem texto como DATABASE_URL= no início."
        ) from exc

    database = parsed.database or ""

    # Corrige placeholders literais anexados ao nome do banco.
    # Exemplos já observados:
    # railway${RAILWAY}
    # railwayAILWAY_PRIVATE_DOMAIN}}:5432/railway
    if database.startswith("railway") and (
        "${" in database
        or "RAILWAY" in database
        or "PRIVATE_DOMAIN" in database
        or "TCP_PROXY" in database
    ):
        database = "railway"
        parsed = parsed.set(database=database)

    if not parsed.database:
        raise RuntimeError("DATABASE_URL não contém o nome do banco de dados.")

    return parsed.render_as_string(hide_password=False)


database_url = normalize_database_url(settings.database_url)

connect_args = (
    {"check_same_thread": False}
    if database_url.startswith("sqlite")
    else {}
)

engine = create_engine(
    database_url,
    pool_pre_ping=True,
    connect_args=connect_args,
)

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
    expire_on_commit=False,
)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
