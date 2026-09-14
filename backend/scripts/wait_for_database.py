"""Wait until the configured database accepts connections before migrations."""

from __future__ import annotations

import logging
import os
import sys
import time

from sqlalchemy import create_engine, text

from app.db.session import normalize_database_url


logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO").upper(),
    format="%(asctime)s | %(levelname)s | cs_platform.deploy | %(message)s",
)
logger = logging.getLogger("cs_platform.deploy")


def main() -> int:
    raw_url = os.getenv("DATABASE_URL", "sqlite:///./cs_platform.db")
    database_url = normalize_database_url(raw_url)
    attempts = int(os.getenv("DATABASE_STARTUP_ATTEMPTS", "30"))
    interval = float(os.getenv("DATABASE_STARTUP_INTERVAL_SECONDS", "2"))

    connect_args = {"check_same_thread": False} if database_url.startswith("sqlite") else {}
    engine = create_engine(database_url, pool_pre_ping=True, connect_args=connect_args)

    for attempt in range(1, attempts + 1):
        try:
            with engine.connect() as connection:
                connection.execute(text("SELECT 1"))
            logger.info("Banco disponível para migrations (tentativa %s/%s).", attempt, attempts)
            return 0
        except Exception as exc:  # pragma: no cover - depends on external service
            if attempt == attempts:
                logger.error("Banco indisponível após %s tentativas: %s", attempts, exc)
                return 1
            logger.warning(
                "Banco ainda indisponível (tentativa %s/%s). Nova tentativa em %.1fs.",
                attempt,
                attempts,
                interval,
            )
            time.sleep(interval)

    return 1


if __name__ == "__main__":
    sys.exit(main())
