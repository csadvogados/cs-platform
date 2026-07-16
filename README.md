# CS Platform Enterprise v5.0.0 — Pacote 01D

## Security Foundation

Este pacote adiciona uma camada de segurança Enterprise sem substituir
a autenticação atual.

## Arquivos novos

```text
backend/app/security/__init__.py
backend/app/security/permissions.py
backend/app/security/password_policy.py
backend/app/security/rbac.py
backend/app/security/session_context.py

backend/tests/security/test_password_policy.py
backend/tests/security/test_permissions.py
backend/tests/security/test_rbac.py
```

## Como aplicar

1. Crie, caso ainda não existam:

```text
backend/app/security
backend/tests/security
```

2. Copie a pasta `backend` do pacote para o repositório.

3. Não substitua nem altere ainda:

```text
backend/app/core/security.py
backend/app/api/routes/auth.py
backend/app/api/routes/users.py
backend/app/models/user.py
```

A integração com as rotas atuais será feita no Pacote 02A — Identity
Integration.

## Testes

Dentro da pasta `backend`:

```bash
pytest tests/security -q
```

## Commit sugerido

```text
Security Foundation 01D - permissions, RBAC and password policy
```
