# Checklist de Deploy — CS Platform v5.4.2

## Railway

1. Confirme que o código publicado contém `backend/alembic/versions/0006_crm_stabilization.py`.
2. Use `/backend` como Root Directory ou mantenha o Dockerfile Path como `/backend/Dockerfile`.
3. Apague qualquer Start Command personalizado no painel.
4. Apague qualquer Pre-deploy Command personalizado no painel.
5. Configure o Healthcheck Path como `/api/v1/health`.
6. Mantenha `DATABASE_URL`, `SECRET_KEY`, credenciais administrativas e demais variáveis já existentes.
7. Faça um novo deploy sem reutilizar uma imagem antiga, quando essa opção estiver disponível.

## Pós-deploy

- `/api/v1/health` deve retornar HTTP 200.
- `/docs` deve abrir o Swagger.
- `/openapi.json` deve retornar HTTP 200.
- O log deve informar a versão `5.4.2`.
- O log do Alembic deve indicar `0006_crm_stabilization (head)`.
