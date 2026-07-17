# CS Platform v5.4.2 — Infrastructure & Deployment (Revisada)

Esta revisão elimina conflitos entre o Railway, o Dockerfile e comandos manuais de deploy.

## Correções

- Dockerfile usa `CMD` em vez de `ENTRYPOINT`, evitando recursão quando o Railway fornece `startCommand`.
- `railway.json` define apenas `/app/docker-entrypoint.sh` como comando de inicialização.
- Nenhum `preDeployCommand`: as migrations são executadas uma única vez pelo entrypoint.
- Uso explícito de `python -m alembic -c /app/alembic.ini`.
- Diagnóstico no log com listagem das migrations presentes na imagem.
- Falha explicativa caso `0006_crm_stabilization.py` não esteja na imagem.
- Validação dinâmica e segura da variável `PORT`.
- Healthcheck com timeout de 300 segundos.

## Configuração Railway

Com Root Directory em `/backend`:

- Dockerfile Path: `/backend/Dockerfile`
- Healthcheck Path: `/api/v1/health`
- Pre-deploy Command: vazio
- Start Command: pode ser apagado no painel; `backend/railway.json` já define `/app/docker-entrypoint.sh`.

Após publicar o commit contendo esta revisão, execute **Redeploy without cache**.
