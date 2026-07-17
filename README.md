# CS Platform v5.1.0 — Pacote 02B.4

## Organization Engine — Integração

Este pacote consolida os subpacotes 02B.1, 02B.2 e 02B.3 e adiciona:

- migration Alembic `0002_organization_engine`;
- bootstrap idempotente;
- registro explícito dos novos modelos;
- repository e service;
- schemas e validators;
- router de organizações preparado;
- testes;
- instruções de ativação segura.

## Decisão de segurança

O router `organizations.py` é incluído no código, mas **não é registrado no
main.py ainda**. A ativação será feita no Pacote 02A, depois que as permissões
administrativas forem integradas à autenticação atual.

Isso evita expor endpoints de administração sem proteção.

## Aplicação

1. Faça backup do projeto e banco.
2. Copie todos os arquivos deste pacote.
3. Substitua:
   - `backend/app/models/organization.py`
   - `backend/app/services/bootstrap.py`
   - `backend/alembic/env.py`
4. Crie os demais arquivos novos.
5. Aplique manualmente os dois pequenos patches descritos em:
   - `backend/app/core/config_patch_02B4.txt`
   - `backend/app/main_patch_02B4.txt`
6. Não registre o router de organizações ainda.
7. Execute:
   - `alembic current`
   - `alembic upgrade head`
8. Faça o deploy.
9. Valide login, usuários, clientes e healthcheck.

## Revision Alembic esperada

A migration utiliza:

- revision: `0002_organization_engine`
- down_revision: `0001_sprint1`

Caso seu `alembic current` mostre outra revisão, não execute a migration antes
de ajustar o `down_revision`.

## Rollback

`alembic downgrade 0001_sprint1`
