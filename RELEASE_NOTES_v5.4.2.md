# CS Platform v5.4.2 — Infrastructure & Deployment

Release de infraestrutura para tornar o deploy no Railway previsível, reproduzível e independente de comandos manuais no painel.

## Correções principais

- `PORT` é interpretada em tempo de execução pelo entrypoint, com fallback seguro para `8000`.
- O Docker inicia a aplicação por um script próprio, evitando que `$PORT` seja enviado literalmente ao Uvicorn.
- O banco é aguardado antes da execução das migrations.
- `alembic upgrade head` passa a ser executado dentro da mesma imagem que contém todas as revisions.
- As revisions disponíveis e a revision ativa são exibidas no log de deploy.
- Removidos `startCommand` e `preDeployCommand` do `railway.json`, eliminando duplicidade e divergência entre imagem, banco e painel.
- Healthcheck padronizado em `/api/v1/health`, com timeout de 120 segundos.
- Dockerfile passa a operar com usuário não privilegiado, logs sem buffer e healthcheck próprio.

## Banco de dados

Esta release não cria nova migration. A revisão esperada permanece:

`0006_crm_stabilization`

## Configuração recomendada no Railway

- Root Directory: `/backend` (quando o repositório contém a pasta `backend`).
- Dockerfile Path: `Dockerfile` se o Root Directory for `/backend`; caso contrário, `/backend/Dockerfile`.
- Start Command: deixar vazio.
- Pre-deploy Command: deixar vazio.
- Healthcheck Path: `/api/v1/health`.

## Validação esperada no log

```text
[deploy] Revisões Alembic disponíveis na imagem:
0006_crm_stabilization (head)
[deploy] Aplicando migrations até head...
[deploy] Revisão Alembic ativa:
0006_crm_stabilization (head)
Iniciando CS Platform versão 5.4.2
Application startup complete
```
