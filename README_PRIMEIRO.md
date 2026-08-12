# CS Platform v5.7.2 — Exportação de clientes

Este pacote adiciona uma exportação segura da base de clientes em CSV.

## O que foi incluído

- botão **Exportar CSV** na tela **Clientes**;
- filtro por status na lista de clientes;
- exportação respeitando o texto pesquisado e o status selecionado;
- arquivo compatível com Excel, com acentos e colunas separadas corretamente;
- proteção contra fórmulas perigosas em células do CSV;
- acesso permitido somente para administrador, supervisor ou superadministrador;
- registro da exportação no **Histórico de atividades**.

## Arquivos que devem ser substituídos

Substitua somente estes quatro arquivos no repositório `csadvogados/cs-platform`:

1. `backend/app/api/routes/clients.py`
2. `frontend/index.html`
3. `frontend/assets/app.js`
4. `frontend/assets/styles.css`

Os arquivos já estão nas pastas corretas dentro deste ZIP.

## Aplicação pelo GitHub

1. Extraia este ZIP no computador.
2. Abra o repositório `csadvogados/cs-platform` no GitHub.
3. Substitua os quatro arquivos acima pelos arquivos deste pacote, mantendo exatamente os mesmos caminhos.
4. Use o seguinte nome no commit:

   `feat: adicionar exportação de clientes v5.7.2`

5. Confirme o commit na branch `main`.
6. Aguarde o Railway concluir os deployments de `cs-platform-api` e `cs-platform-web`.

## Não altere no Railway

Esta versão não exige:

- migration do banco de dados;
- variável nova;
- mudança em `railway.json`;
- mudança em `Dockerfile`;
- comando manual no Console.

## Teste depois do deployment

1. Abra `https://cs-platform-web-production.up.railway.app/`.
2. Pressione `Ctrl + F5` para carregar os arquivos novos.
3. Entre com uma conta de administrador ou supervisor.
4. Clique em **Clientes**.
5. Confira se aparecem o campo **Status** e o botão **Exportar CSV**.
6. Digite parte do nome de um cliente ou selecione um status.
7. Clique em **Exportar CSV**.
8. Confira na pasta **Downloads** o arquivo `clientes_AAAA-MM-DD.csv`.
9. Abra o arquivo no Excel e confirme que cada informação ficou em sua própria coluna.
10. Abra **Histórico** e confirme a atividade **Exportou — Cliente**.

O arquivo exportado contém somente clientes da organização da pessoa conectada.

## Validações realizadas

- sintaxe Python e JavaScript;
- ordem correta da rota de exportação;
- permissão `client.export`;
- isolamento por organização;
- filtros por pesquisa e status;
- codificação UTF-8 com BOM para Excel;
- separador `;` compatível com Excel em português;
- neutralização de conteúdo iniciado por `=`, `+`, `-` ou `@`;
- clique real no botão em navegador local controlado;
- estrutura e hashes SHA-256 do ZIP.
