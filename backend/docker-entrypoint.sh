#!/bin/sh
set -eu

PORT="${PORT:-8000}"
HOST="${HOST:-0.0.0.0}"
WEB_CONCURRENCY="${WEB_CONCURRENCY:-1}"
MIGRATIONS_ENABLED="${MIGRATIONS_ENABLED:-true}"

case "$PORT" in
  ''|*[!0-9]*)
    echo "ERRO: PORT deve ser um número inteiro; valor recebido: '$PORT'" >&2
    exit 64
    ;;
esac

if [ "$MIGRATIONS_ENABLED" = "true" ] || [ "$MIGRATIONS_ENABLED" = "1" ]; then
  echo "[deploy] Aguardando disponibilidade do banco..."
  python scripts/wait_for_database.py

  echo "[deploy] Revisões Alembic disponíveis na imagem:"
  alembic heads

  echo "[deploy] Aplicando migrations até head..."
  alembic upgrade head

  echo "[deploy] Revisão Alembic ativa:"
  alembic current
else
  echo "[deploy] Migrations desabilitadas por MIGRATIONS_ENABLED=$MIGRATIONS_ENABLED"
fi

if [ "$#" -gt 0 ]; then
  exec "$@"
fi

exec python -m uvicorn app.main:app \
  --host "$HOST" \
  --port "$PORT" \
  --workers "$WEB_CONCURRENCY" \
  --proxy-headers \
  --forwarded-allow-ips="*"
