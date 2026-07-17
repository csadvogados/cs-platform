# Checklist — v5.4.2 revisada

1. Substitua integralmente os arquivos do repositório pelos deste pacote.
2. Confirme no GitHub a existência de `backend/alembic/versions/0006_crm_stabilization.py`.
3. Confirme no GitHub que `backend/railway.json` não contém `preDeployCommand`.
4. No Railway, apague o Pre-deploy Command manual.
5. Apague o Start Command manual ou deixe `/app/docker-entrypoint.sh`.
6. Root Directory: `/backend`.
7. Dockerfile Path: `/backend/Dockerfile`.
8. Healthcheck Path: `/api/v1/health`.
9. Faça `Redeploy without cache`.
10. Procure no log por `[deploy] CS Platform v5.4.2 revisada` e pela listagem de `0006_crm_stabilization.py`.
