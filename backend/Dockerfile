FROM python:3.12-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PORT=8000 \
    HOST=0.0.0.0 \
    WEB_CONCURRENCY=1 \
    MIGRATIONS_ENABLED=true

WORKDIR /app

RUN addgroup --system app && adduser --system --ingroup app app

COPY requirements.txt ./requirements.txt
RUN python -m pip install --upgrade pip \
    && python -m pip install --no-cache-dir -r requirements.txt

COPY --chown=app:app . .
RUN chmod 0755 /app/docker-entrypoint.sh \
    && test -f /app/alembic/versions/0006_crm_stabilization.py

USER app

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=45s --retries=5 \
  CMD-SHELL python -c "import os, urllib.request; urllib.request.urlopen('http://127.0.0.1:' + os.getenv('PORT','8000') + '/api/v1/health', timeout=4)" || exit 1

# Comando padrão compatível com substituição pelo Railway.
CMD ["/app/docker-entrypoint.sh"]
