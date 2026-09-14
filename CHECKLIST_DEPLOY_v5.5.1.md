# Checklist de deploy — v5.5.1

1. Confirmar que o deploy usa `backend/Dockerfile`.
2. Confirmar que o Dockerfile contém `HEALTHCHECK ... CMD python -c` e não contém `CMD-SHELL`.
3. Confirmar presença de `backend/alembic/versions/0007_cs_captacao_mvp.py`.
4. Manter `DATABASE_URL`, `SECRET_KEY` e credenciais administrativas configuradas no ambiente.
5. Publicar a v5.5.1.
6. Nos logs, confirmar: banco disponível → `alembic upgrade head` → revisão `0007_cs_captacao_mvp` → Uvicorn iniciado.
7. Confirmar `GET /api/v1/health` = 200.
8. Confirmar `/docs` e testar autenticação/CRM antes de liberar uso operacional.
