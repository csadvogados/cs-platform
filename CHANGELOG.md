# Changelog

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
