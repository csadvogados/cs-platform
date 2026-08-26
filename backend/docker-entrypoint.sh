#!/bin/sh
set -eu

cd /app

PORT="${PORT:-8000}"
HOST="${HOST:-0.0.0.0}"
WEB_CONCURRENCY="${WEB_CONCURRENCY:-1}"

echo "[deploy] CS-Platform-v5.19.0"
echo "[deploy] Waiting for database"
python -m scripts.wait_for_database

echo "[deploy] Alembic heads"
python -m alembic -c /app/alembic.ini heads

echo "[deploy] Applying migrations"
python -m alembic -c /app/alembic.ini upgrade head

echo "[deploy] Current revision"
python -m alembic -c /app/alembic.ini current

echo "[deploy] Starting Uvicorn on ${HOST}:${PORT}"
exec python -m uvicorn app.main:app \
  --host "$HOST" \
  --port "$PORT" \
  --workers "$WEB_CONCURRENCY" \
  --proxy-headers
