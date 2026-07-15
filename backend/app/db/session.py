from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings


database_url = settings.database_url.strip()

# O Railway normalmente fornece a URL como "postgresql://".
# Como o projeto utiliza psycopg 3, ajustamos explicitamente o dialeto
# para impedir que o SQLAlchemy tente carregar o driver psycopg2.
if database_url.startswith("postgresql://"):
    database_url = database_url.replace(
        "postgresql://",
        "postgresql+psycopg://",
        1,
    )

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
