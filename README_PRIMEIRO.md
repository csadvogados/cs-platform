# Correção da v5.14.0 — erro 500 ao salvar organização

Esta correção substitui somente um arquivo da API.

## Arquivo a substituir no GitHub

`backend/app/api/routes/financial.py`

Use o arquivo de mesmo caminho existente neste pacote.

## Commit sugerido

`fix: corrigir salvamento da fila de cobranças v5.14.0`

Depois do commit, aguarde apenas o deploy do serviço `cs-platform-api` no Railway.
Não é necessário alterar variáveis, comandos ou o banco de dados.

## Teste após o deploy

1. Atualize a página da plataforma.
2. Abra **Cobranças**.
3. Clique em **Organizar**.
4. Escolha um responsável e uma prioridade.
5. Clique em **Salvar organização**.

O nome do responsável e a prioridade devem aparecer na cobrança sem erro 500.
