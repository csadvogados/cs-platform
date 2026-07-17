# Checklist de Deploy v5.4.1

1. Fazer backup do PostgreSQL.
2. Confirmar que a versão atual é v5.4.0 e o banco está em `0005_crm_enterprise`.
3. Publicar este pacote.
4. Executar `alembic upgrade head`.
5. Confirmar `0006_crm_stabilization (head)`.
6. Executar `pytest -q`.
7. Validar `/api/v1/health`, `/docs` e `/openapi.json`.
8. No Swagger, testar `/api/v1/crm/summary` e os filtros de tarefas.
