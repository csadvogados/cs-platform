# CS Platform v5.6.6 — gestão completa do CRM

Este pacote acrescenta ações seguras para administrar os registros do CRM:

- editar e apagar contatos;
- editar e apagar oportunidades;
- mudar a etapa de uma oportunidade diretamente no quadro;
- visualizar também as etapas **Ganha** e **Perdida**;
- editar, concluir e apagar tarefas;
- atualizar automaticamente os totais do CRM e do painel após cada alteração;
- pedir confirmação antes de qualquer exclusão.

## Como aplicar no GitHub

Substitua exatamente estes três arquivos no repositório `csadvogados/cs-platform`:

1. `frontend/index.html`
2. `frontend/assets/app.js`
3. `frontend/assets/styles.css`

Use este nome no commit:

`feat: adicionar gestão completa do CRM v5.6.6`

O commit deverá gerar o deployment do serviço `cs-platform-web` no Railway. Se o serviço da API aparecer como **Skipped / No changes to watched files**, isso é normal nesta versão.

Aguarde o deployment do `cs-platform-web` ficar verde. Depois, abra o sistema e pressione `Ctrl + F5`.

Não altere banco, migrations, variáveis, `railway.json`, `Dockerfile`, `docker-entrypoint.sh` ou `nginx.conf`. A API atual já possui as rotas necessárias e esta versão não exige migration.

## Teste depois do deploy

1. Entre em **CRM**.
2. Em **Oportunidades**, clique em **Editar**, altere um valor e salve.
3. Use o campo **Etapa** no cartão para mover a oportunidade entre as colunas.
4. Em **Tarefas**, clique em **Editar** e depois em **Concluir**.
5. Cadastre registros de teste e confirme que o botão **Apagar** pede confirmação.
6. Confira se os totais do CRM e da **Visão geral** mudam automaticamente.
7. Abra qualquer janela de cadastro e confirme que o botão **X** fecha normalmente.

## Conferência

O arquivo `SHA256SUMS.txt` contém os códigos SHA-256 dos três arquivos substituídos.
