# CS Platform v5.7.6 — Assistente de importação

Esta atualização deixa a importação de clientes mais simples e segura.

## O que foi adicionado

- Botão **Baixar modelo CSV** dentro da janela de importação.
- Modelo compatível com Excel e com todas as colunas aceitas pela plataforma.
- Botão **Baixar relatório de erros** quando a conferência encontrar linhas inválidas ou duplicadas.
- Relatório com linha, nome, CPF, situação e descrição do problema.
- Proteção do relatório contra fórmulas perigosas em arquivos CSV.
- A conferência e os downloads não gravam clientes na base.

## Arquivos que devem ser substituídos

Substitua exatamente estes quatro arquivos no GitHub:

1. `backend/app/api/routes/clients.py`
2. `frontend/index.html`
3. `frontend/assets/app.js`
4. `frontend/assets/styles.css`

Mantenha cada arquivo na pasta indicada acima.

## Nome do commit

Use este nome:

`feat: adicionar modelo e relatório de importação v5.7.6`

## Railway

Depois do commit, aguarde os serviços **cs-platform-api** e **cs-platform-web** concluírem o deploy.

Esta versão:

- não possui migration de banco de dados;
- não altera variáveis do Railway;
- não altera `railway.json`, `Dockerfile` ou comandos de inicialização.

## Teste simples depois do deploy

1. Entre no sistema e clique em **Clientes**.
2. Clique em **Importar CSV**.
3. Clique em **Baixar modelo CSV** e confirme que o arquivo abre com os títulos das colunas.
4. Escolha um CSV e clique em **Conferir arquivo**.
5. Se existirem linhas com problema, clique em **Baixar relatório de erros**.
6. Abra o relatório e confira as colunas **Linha**, **Nome**, **CPF**, **Situação** e **Erros**.
7. Não marque a autorização durante este primeiro teste. Feche a janela.

Se o CSV estiver totalmente correto, o botão de relatório de erros ficará oculto. Isso é o comportamento esperado.

## Verificação do pacote

O arquivo `SHA256SUMS.txt` contém os códigos de integridade de todos os arquivos desta atualização.
