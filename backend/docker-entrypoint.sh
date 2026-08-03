#!/bin/sh
set -eu

PORT="${PORT:-8000}"
HOST="${HOST:-0.0.0.0}"
WEB_CONCURRENCY="${WEB_CONCURRENCY:-1}"
MIGRATIONS_ENABLED="${MIGRATIONS_ENABLED:-true}"

case "$PORT" in
  ''|*[!0-9]*)
    echo "[deploy][erro] PORT deve ser um número inteiro; recebido: '$PORT'" >&2
    exit 64
    ;;
esac

cd /app

echo "[deploy] CS Platform v5.4.2"

if [ ! -f /app/alembic/versions/0006_crm_stabilization.py ]; then
  echo "[deploy][erro] A imagem não contém 0006_crm_stabilization.py." >&2
  exit 66
fi

if [ "$MIGRATIONS_ENABLED" = "true" ] || [ "$MIGRATIONS_ENABLED" = "1" ]; then
  echo "[deploy] Aguardando o banco de dados..."
  python -m scripts.wait_for_database

  echo "[deploy] Validando a cabeça do Alembic..."
  heads="$(python -m alembic -c /app/alembic.ini heads)"
  printf '%s\n' "$heads"
  printf '%s\n' "$heads" | grep -q "0006_crm_stabilization (head)" || {
    echo "[deploy][erro] A cabeça esperada do Alembic não foi encontrada." >&2
    exit 67
  }

  echo "[deploy] Ap
