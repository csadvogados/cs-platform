from __future__ import annotations

from collections.abc import Generator

from sqlalchemy.orm import Session

from app.db.session import SessionLocal


def get_database_session() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


__all__ = ["get_database_session"]
