# CS Platform v5.3.0 — Enterprise User Management

## Entrega
- RBAC persistente com perfis e permissões por organização.
- Convites com token seguro, expiração e aceite público.
- Gestão de usuários com pesquisa, paginação, bloqueio, desbloqueio e exclusão lógica.
- Registro de sessões e base para encerramento remoto.
- Histórico de senhas e campos de governança de credenciais.
- Migration Alembic linear `0004_enterprise_user_management`.
- Bootstrap idempotente de permissões e perfis padrão.

## Upgrade
1. Fazer backup do banco.
2. Definir as variáveis de ambiente usuais.
3. Executar `alembic upgrade head`.
4. Executar `pytest -q`.
5. Implantar no Railway.
