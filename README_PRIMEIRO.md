# CS Platform v5.16.0 — Gestão de carga da equipe

Este pacote contém somente os 7 arquivos que devem ser substituídos no GitHub.

## Como aplicar

No repositório `csadvogados/cs-platform`, substitua os arquivos mantendo exatamente as mesmas pastas:

1. `backend/app/api/routes/financial.py`
2. `backend/app/core/constants.py`
3. `backend/app/schemas/financial.py`
4. `backend/docker-entrypoint.sh`
5. `frontend/index.html`
6. `frontend/assets/app.js`
7. `frontend/assets/styles.css`

Use este nome no commit:

`feat: adicionar gestão de carga e distribuição de cobranças v5.16.0`

Não há nova migração de banco nesta versão. Não altere comandos, variáveis ou configurações do Railway.

## Depois do commit

1. Aguarde os deployments `cs-platform-api` e `cs-platform-web` ficarem verdes.
2. Abra o sistema e pressione `Ctrl + F5`.
3. Entre como administrador ou supervisor e abra **Cobranças**.
4. Expanda **Carga da equipe**.
5. Marque pelo menos duas cobranças abertas e clique em **Distribuir selecionadas**.
6. Escolha pelo menos dois responsáveis e confirme.
7. Confira se a fila foi dividida e se os totais foram atualizados automaticamente.
8. Use **Ver fila** para conferir as cobranças de cada responsável.
9. Confira no **Histórico** o registro individual das alterações.

Cobranças pagas e canceladas não entram na distribuição.
