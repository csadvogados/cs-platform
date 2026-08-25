# CS Platform v5.16.1 — Correção do botão Ver fila

Este pacote contém os 7 arquivos que devem ser substituídos no GitHub.

## Como aplicar

Substitua os arquivos mantendo exatamente as mesmas pastas:

1. `backend/app/api/routes/financial.py`
2. `backend/app/core/constants.py`
3. `backend/app/schemas/financial.py`
4. `backend/docker-entrypoint.sh`
5. `frontend/index.html`
6. `frontend/assets/app.js`
7. `frontend/assets/styles.css`

Use este nome no commit:

`fix: corrigir filtro Ver fila v5.16.1`

Não há nova migração de banco. Não altere comandos ou variáveis do Railway.

## Teste depois do deploy

1. Aguarde API e interface ficarem verdes.
2. Abra o sistema e pressione `Ctrl + F5`.
3. Abra **Cobranças** e expanda **Carga da equipe**.
4. Clique em **Ver fila** ao lado de um responsável.
5. A tela deverá descer até a lista, selecionar o responsável no filtro e mostrar a quantidade encontrada.
