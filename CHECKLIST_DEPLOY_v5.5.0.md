# Checklist de homologação/deploy — v5.5.0

1. Faça backup do banco e preserve o pacote/release v5.4.2 atual.
2. Publique os arquivos da v5.5.0 em branch de homologação.
3. Confirme `backend/alembic/versions/0007_cs_captacao_mvp.py`.
4. Confirme que `backend/docker-entrypoint.sh` e `backend/Dockerfile` validam a migration 0007.
5. Instale as dependências de `backend/requirements.txt`.
6. Execute `python -m alembic -c backend/alembic.ini heads` e confirme `0007_cs_captacao_mvp` como único head.
7. Em homologação, execute `alembic upgrade head`.
8. Execute `pytest -q`; resultado esperado nesta entrega: 48 testes aprovados.
9. Teste login, criação de cliente/lead, oportunidade, mudança de etapa, histórico, tarefa, pipeline, dashboard e conversão.
10. Confirme que uma oportunidade de serviço `CS Recupera` cria um único caso ao converter.
11. Verifique `/api/v1/health`, `/docs` e `/openapi.json`.
12. Somente após homologação, faça o deploy de produção e confira no log a revisão Alembic ativa.

## Não fazer

- não executar downgrade da 0007 em produção sem backup e janela de manutenção;
- não substituir diretamente o banco de produção por banco de teste;
- não criar manualmente tabelas/colunas que já pertencem à migration;
- não apagar as migrations 0005 e 0006.
