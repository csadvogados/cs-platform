# CS Platform v5.19.0 — LEIA PRIMEIRO

Este pacote adiciona a **Central de alertas operacionais**.

## Como instalar

1. Abra o repositório `csadvogados/cs-platform` no GitHub.
2. Substitua os sete arquivos do pacote, mantendo exatamente as mesmas pastas.
3. Confirme o commit com a mensagem:

   `feat: adicionar central de alertas operacionais v5.19.0`

4. Aguarde o deploy do `cs-platform-api` terminar com sucesso.
5. Aguarde o deploy do `cs-platform-web` terminar com sucesso.
6. Não preencha o campo **Pre-deploy Command**. Esta versão não possui migração de banco.

## Como testar

1. Acesse a plataforma e faça login.
2. Confira o sino no cabeçalho e clique nele.
3. Confira o contador e os alertas de cobranças, promessas, acompanhamentos e tarefas.
4. Clique em **Cobranças críticas**. A tela Cobranças deve abrir com o filtro **Crítica**.
5. Clique em **Tarefas do CRM atrasadas**. O CRM deve abrir na aba **Tarefas**, com o filtro **Atrasadas**.
6. Clique em **Atualizar alertas** e confirme a mensagem de atualização.
7. Em Configurações, confirme `5.19.0`, API online e banco de dados OK.

## Arquivos incluídos

- `backend/app/api/routes/financial.py`
- `backend/app/core/constants.py`
- `backend/app/schemas/financial.py`
- `backend/docker-entrypoint.sh`
- `frontend/index.html`
- `frontend/assets/app.js`
- `frontend/assets/styles.css`
- `README_PRIMEIRO.md`
- `SHA256SUMS.txt`
