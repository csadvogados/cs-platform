# CS Platform v5.18.0 — Fila inteligente de cobranças

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

`feat: adicionar fila inteligente de cobranças v5.18.0`

Não há nova migração de banco. Não altere comandos ou variáveis do Railway.

## Teste depois do deploy

1. Aguarde API e interface ficarem verdes.
2. Abra o sistema e pressione `Ctrl + F5`.
3. Abra **Cobranças**.
4. Confira a nova coluna **Ação recomendada** e os níveis de atenção.
5. Teste o filtro **Nível de atenção** e as opções de ordenação.
6. Selecione **Ordem recomendada** e clique em **Atender próxima**.
7. Confirme que a janela de registro de contato foi aberta para a cobrança prioritária.
