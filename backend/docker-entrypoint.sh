#!/bin/sh
set -eu

cd /app

echo [deploy] CS-Platform-v5.4.2
echo [deploy] Waiting-for-database
python -m scripts.wait_for_database

echo [deploy] Alembic-heads
python -m alembic -c /app/alembic.ini heads

echo [deploy] Applying-migrations
python -m alembic -c /app/alembic.ini upgrade head

echo [deploy] Current-revision
python -m alembic -c /app/alembic.ini current

echo [deploy] Starting-Uvicorn-on-po
exec python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 1 --proxy-headers
