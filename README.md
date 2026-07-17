# CS Platform v5.2.0 — Enterprise Security & Multi-Tenant

Pacote incremental para aplicar sobre o backend **após o 02B.4**.

## Entregas

- migration Alembic de merge dos heads `0002_auth_enterprise` e `0002_organization_engine`;
- `IdentityContext` com usuário, organização, perfil e permissões;
- validação dos claims `org` e `role` contra o banco;
- bloqueio de login quando a organização estiver inativa;
- `/api/v1/auth/me` enriquecido;
- router de organizações protegido e ativável por configuração;
- testes de identidade e tokens inconsistentes;
- versão da aplicação atualizada para `5.2.0`.

## Aplicação

1. Faça backup/commit do projeto atual.
2. Copie o conteúdo da pasta `backend/` deste pacote sobre a pasta `backend/` do projeto.
3. Não apague nem edite as migrations `0002_*` já existentes.
4. Confirme que o novo arquivo existe:
   `alembic/versions/0003_merge_auth_organization.py`.
5. Execute:

```bash
alembic heads
```

O resultado esperado é um único head:

```text
0003_merge_auth_organization (head)
```

6. Execute:

```bash
alembic upgrade head
pytest -q
```

7. Ative o módulo no ambiente:

```env
ORGANIZATION_API_ENABLED=true
```

8. Faça o deploy.

## Segurança

O pacote não implementa filtro SQL global implícito. Esse padrão pode ocultar consultas administrativas e produzir efeitos inesperados. O isolamento permanece explícito por `organization_id`, reforçado pelo `IdentityContext` e por dependências de autorização. Nos próximos módulos, repositories tenant-aware devem receber obrigatoriamente o `organization_id` do contexto.

## Rollback

A migration `0003_merge_auth_organization` é apenas de merge e não altera tabelas. O downgrade retorna a árvore para os dois heads anteriores, o que não é recomendado em produção após novas migrations dependerem dela.

## Railway — v5.4.2

A inicialização de produção é controlada por `backend/docker-entrypoint.sh`. No Railway, deixe os campos **Start Command** e **Pre-deploy Command** vazios. O entrypoint aguarda o banco, aplica `alembic upgrade head` e inicia o Uvicorn usando a variável dinâmica `PORT`.

Consulte `CHECKLIST_DEPLOY_v5.4.2.md` antes da publicação.
