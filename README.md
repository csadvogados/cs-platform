# CS Platform Enterprise v5.0.0 — Pacote 01B

## Core Infrastructure

Este pacote integra o Foundation Core ao projeto atual, preservando:

- autenticação;
- bootstrap;
- Swagger;
- PostgreSQL;
- Railway;
- routers existentes.

## Como aplicar

1. Faça backup de:
   - backend/app/core/config.py
   - backend/app/db/base.py
   - backend/app/main.py

2. Copie a pasta backend deste pacote para o repositório.

3. Confirme:
   - substituição de config.py;
   - substituição de db/base.py;
   - substituição de main.py;
   - criação de core/logging.py;
   - criação de core/dependencies.py;
   - criação dos testes.

4. Não altere:
   - backend/alembic/env.py;
   - modelos atuais;
   - migrations existentes.

## Variáveis Railway opcionais

LOG_LEVEL=INFO
LOG_JSON=false
DEBUG=false
TIMEZONE=America/Sao_Paulo

## Testes

pytest tests/core -q

## Commit sugerido

Core Infrastructure 01B - config, logging, dependencies e base integration
