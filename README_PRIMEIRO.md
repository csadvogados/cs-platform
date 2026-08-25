# CS Platform v5.14.0 — Fila de trabalho de cobranças

Esta versão transforma a Central de cobranças em uma fila organizada de trabalho da equipe.

## Novidades

- definição de responsável para cada cobrança;
- prioridades **Baixa**, **Normal**, **Alta** e **Urgente**;
- botão **Minhas cobranças**;
- filtros por responsável e prioridade;
- indicadores de cobranças urgentes e sem responsável;
- exibição do responsável e da prioridade na lista;
- alteração da fila restrita a administradores e supervisores;
- registro das mudanças no Histórico de atividades;
- manutenção dos relatórios gerenciais da v5.13.0.

## Migração do banco

A versão inclui a migração `0013_collection_queue`, ligada à migração `0012_action_cancellation`.

O Railway executará essa migração automaticamente durante a inicialização da API.

## Arquivos que devem ser substituídos

1. `backend/alembic/versions/0013_collection_queue.py`
2. `backend/app/api/routes/financial.py`
3. `backend/app/core/constants.py`
4. `backend/app/models/financial.py`
5. `backend/app/schemas/financial.py`
6. `backend/docker-entrypoint.sh`
7. `frontend/index.html`
8. `frontend/assets/app.js`
9. `frontend/assets/styles.css`

Use no commit:

`feat: adicionar fila de trabalho de cobranças v5.14.0`

## Teste recomendado

1. Abra **Cobranças**.
2. Clique em **Organizar** em uma cobrança aberta.
3. Escolha um responsável, selecione **Urgente** e salve.
4. Confirme o nome e a prioridade na lista.
5. Confira se o indicador de cobranças urgentes aumentou.
6. Teste **Minhas cobranças**.
7. Teste os filtros por responsável e prioridade.
8. Remova o responsável e confirme o indicador **sem responsável**.
9. Abra **Histórico** e confirme o registro da atualização da parcela.
