# CS Platform v5.7.5 — Paginação e busca de clientes

Este pacote contém uma atualização verificada para a tela **Clientes**.

## O que muda

- A pesquisa passa a consultar toda a base de clientes, e não somente os primeiros 100 registros.
- A lista mostra o total correto de resultados.
- Foram adicionados os botões **Anterior** e **Próxima**.
- É possível escolher 10, 25, 50 ou 100 clientes por página.
- Ao trocar a pesquisa ou o status, a lista volta automaticamente para a primeira página.
- Os seletores de cliente do CRM continuam sendo carregados normalmente.

## Arquivos que devem ser substituídos

Substitua exatamente estes cinco arquivos no GitHub:

1. `backend/app/api/routes/clients.py`
2. `backend/app/schemas/client.py`
3. `frontend/index.html`
4. `frontend/assets/app.js`
5. `frontend/assets/styles.css`

Mantenha cada arquivo na pasta indicada acima.

## Nome do commit

Use este nome:

`feat: adicionar busca e paginação de clientes v5.7.5`

## Railway

Depois do commit, aguarde os serviços **cs-platform-api** e **cs-platform-web** concluírem o deploy.

Esta versão:

- não possui migration de banco de dados;
- não altera variáveis do Railway;
- não altera `railway.json`, `Dockerfile` ou comandos de inicialização.

## Teste simples depois do deploy

1. Abra o sistema e entre normalmente.
2. Clique em **Clientes**.
3. Confira se aparece o total de clientes e `Página 1 de ...`.
4. Em **Por página**, selecione `10`.
5. Se houver mais de 10 clientes, clique em **Próxima** e depois em **Anterior**.
6. Pesquise um cliente pelo nome e confira se o total muda.
7. Limpe a pesquisa e teste o filtro **Status**.
8. Abra **Ver detalhes** de um cliente para confirmar o acesso normal.

Se a base tiver menos de 11 clientes, o botão **Próxima** ficará desativado. Isso é o comportamento correto.

## Verificação do pacote

O arquivo `SHA256SUMS.txt` contém os códigos de integridade de todos os arquivos desta atualização.
