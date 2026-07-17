#!/bin/sh
set -eu

PORT="${PORT:-8000}"
HOST="${HOST:-0.0.0.0}"
WEB_CONCURRENCY="${WEB_CONCURRENCY:-1}"
MIGRATIONS_ENABLED="${MIGRATIONS_ENABLED:-true}"

case "$PORT" in
  ''|*[!0-9]*)
    echo "[deploy][erro] PORT deve ser inteiro; recebido: '$PORT'" >&2
    exit 64
    ;;
esac

cd /app

echo "[deploy] CS Platform v5.4.2 revisada"
echo "[deploy] Diretório atual: $(pwd)"
echo "[deploy] Porta: $PORT"
echo "[deploy] Arquivos de migration presentes:"
find /app/alembic/versions -maxdepth 1 -type f -name '*.py' -print | sort

if [ ! -f /app/alembic/versions/0006_crm_stabilization.py ]; then
  echo "[deploy][erro] A imagem não contém 0006_crm_stabilization.py." >&2
  echo "[deploy][erro] Confirme o commit implantado, Root Directory=/backend e Dockerfile Path=/backend/Dockerfile." >&2
  exit 66
fi

if [ "$MIGRATIONS_ENABLED" = "true" ] || [ "$MIGRATIONS_ENABLED" = "1" ]; then
  echo "[deploy] Aguardando banco..."
  python /app/scripts/wait_for_database.py

  echo "[deploy] Heads Alembic disponíveis:"
  python -m alembic -c /app/alembic.ini heads

  echo "[deploy] Aplicando migrations até head..."
  python -m alembic -c /app/alembic.ini upgrade head

  echo "[deploy] Revisão ativa:"
  python -m alembic -c /app/alembic.ini current
else
  echo "[deploy] Migrations desabilitadas: MIGRATIONS_ENABLED=$MIGRATIONS_ENABLED"
fi

echo "[deploy] Iniciando Uvicorn..."
exec python -m uvicorn app.main:app \
  --host "$HOST" \
  --port "$PORT" \
  --workers "$WEB_CONCURRENCY" \
  --proxy-headers \
  --forwarded-allow-ips="*"
