# CS Platform v5.5.1 — Docker Healthcheck Hotfix

## Motivo

O deploy falhou durante o parse do `backend/Dockerfile` com a mensagem:

`Unknown type "CMD-SHELL" in HEALTHCHECK (try CMD)`

## Correção

O `HEALTHCHECK` passou de `CMD-SHELL` para `CMD`, preservando a verificação HTTP em `/api/v1/health`.

## Banco de dados

- Não cria nova migration.
- Mantém `0007_cs_captacao_mvp` como head esperado.
- Nenhuma alteração destrutiva.

## Deploy

Publicar o pacote v5.5.1. O `docker-entrypoint.sh` continuará aguardando o PostgreSQL, executando `alembic upgrade head` e iniciando o Uvicorn.
