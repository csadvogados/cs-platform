# CS Platform v5.17.0 — Envelhecimento da inadimplência

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

`feat: adicionar faixas de atraso nas cobranças v5.17.0`

Não há nova migração de banco. Não altere comandos ou variáveis do Railway.

## Teste depois do deploy

1. Aguarde API e interface ficarem verdes.
2. Abra o sistema e pressione `Ctrl + F5`.
3. Abra **Cobranças**.
4. Confira as quatro faixas do painel **Envelhecimento da inadimplência**.
5. Clique em uma faixa e confirme que a lista foi filtrada.
6. Clique em **Limpar** e confirme o retorno de todas as cobranças.
