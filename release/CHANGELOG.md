# v5.4.2

- Deploy Railway consolidado no Docker entrypoint.
- Suporte correto à variável dinâmica `PORT`.
- Espera ativa do PostgreSQL antes das migrations.
- Alembic executado dentro da imagem, sem comando duplicado no Railway.
- Healthcheck e política de reinício padronizados.
- Diagnóstico de revisions Alembic incluído nos logs.
- Nenhuma alteração destrutiva ou nova migration.

# v5.4.1

CRM estabilizado, validado e otimizado com índices compostos, CRUD ampliado e novos indicadores.

# v5.4.0
- CRM Enterprise: contatos, interações, oportunidades, tarefas e dashboard.

# v5.3.1
- Segurança HTTP, rate limiting e observabilidade OpenMetrics.

# CHANGELOG — Pacote 01D

## Adicionado

- Catálogo de permissões.
- Matriz RBAC inicial.
- Verificação de permissões.
- Política de senha.
- Contexto de segurança por requisição.
- Testes unitários de segurança.

## Não alterado

- Login atual.
- JWT atual.
- Refresh token atual.
- Rotas protegidas atuais.
- Banco de dados.
