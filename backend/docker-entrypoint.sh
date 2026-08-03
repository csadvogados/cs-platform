#!/bin/sh
set -eu

cd /app

PORT="${PORT:-8000}"
HOST="${HOST:-0.0.0.0}"
WEB_CONCURRENCY="${WEB_CONCURRENCY:-1}"
MIGRATIONS_ENABLED="${MIGRATIONS_ENABLED:-true}"

case "$PORT" in
  ''|*[!0-9]*)
    echo "[deploy][error] PORT must be an integer" >&2
    exit 64
    ;;
esac

if [ ! -f /app/alembic/versions/0006_crm_stabilization.py ]; then
  echo "[deploy][error] Missing migration 0006_crm_stabilization.py" >&2
  exit 66
fi

echo "[deploy] CS Platform v5.4.2"

if [ "$MIGRATIONS_ENABLED" = "true" ] || [ "$MIGRATIONS_ENABLED" = "1" ]; then
  echo "[deploy] Waiting for database"
  python -m scripts.wait_for_database

  echo "[deploy] Alembic heads"
  python -m alembic -c /app/alembic.ini heads

  echo "[deploy] Applying migrations"
  python -m alembic -c /app/alembic.ini upgrade head

  echo "[deploy] Current revision"
  python -m alembic -c /app/alembic.ini current
fi

echo "[deploy] Starting Uvicorn
