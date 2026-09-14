# v5.5.0

- CS Captação / CRM MVP implementado sobre o CRM Enterprise.
- Funil NOVO, CONTATADO, QUALIFICADO, PROPOSTA, CONVERTIDO e PERDIDO.
- Pipeline, detalhe do lead, histórico de etapa, dashboard e filtros comerciais.
- Conversão para cliente contratado e criação de caso CS Recupera.
- RBAC específico `crm.*` e auditoria com valores anteriores/posteriores.
- Migration `0007_cs_captacao_mvp`.
- 48 testes aprovados na validação manual.

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

# Changelog

## 5.3.0 — Enterprise User Management

- RBAC persistente por organização.
- Catálogo de permissões e perfis padrão.
- Convites de usuários com token seguro e expiração.
- Pesquisa, paginação, bloqueio, desbloqueio e exclusão lógica de usuários.
- Estrutura de sessões e histórico de senhas.
- Migration Alembic `0004_enterprise_user_management`.
- Testes de regressão e integração.

## 5.2.0 — Enterprise Security & Multi-Tenant

### Adicionado
- IdentityContext.
- Schema enriquecido de identidade.
- Migration de merge Alembic.
- Proteção multi-tenant do Organization Router.
- Verificação de organização ativa.
- Validação de claims de organização e perfil.
- Testes de segurança.

### Alterado
- `/auth/me` passa a retornar organização e permissões.
- Organization Router pode ser ativado por `ORGANIZATION_API_ENABLED`.
- Versão da API atualizada para 5.2.0.
