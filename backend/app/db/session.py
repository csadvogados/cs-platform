from sqlalchemy import create_engine
from sqlalchemy.engine import make_url
from sqlalchemy.orm import sessionmaker

from app.core.config import settings


def normalize_database_url(raw_url: str) -> str:
    if not raw_url or not raw_url.strip():
        raise RuntimeError(
            "DATABASE_URL não foi definida no ambiente."
        )

    database_url = raw_url.strip().strip('"').strip("'")

    if database_url.startswith("postgres://"):
        database_url = database_url.replace(
            "postgres://",
            "postgresql://",
            1,
        )

    if database_url.startswith("postgresql://"):
        database_url = database_url.replace(
            "postgresql://",
            "postgresql+psycopg://",
            1,
        )

    if database_url.startswith("sqlite"):
        return database_url

    try:
        parsed_url = make_url(database_url)
    except Exception as exc:
        raise RuntimeError(
            "DATABASE_URL inválida. Verifique a variável no Railway."
        ) from exc

    database_name = parsed_url.database or ""

    if (
        database_name.startswith("railway")
        and (
            "${" in database_name
            or "RAILWAY" in database_name
            or "PRIVATE_DOMAIN" in database_name
            or "TCP_PROXY" in database_name
        )
    ):
        parsed_url = parsed_url.set(database="railway")

    return parsed_url.render_as_string(hide_password=False)


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
