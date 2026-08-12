# CS Platform v5.7.3 — Importação de clientes por CSV

Este pacote adiciona a importação segura de clientes a partir de um arquivo CSV.

## O que foi incluído

- botão **Importar CSV** na tela **Clientes**;
- leitura de arquivos CSV separados por `;` ou `,`;
- compatibilidade com arquivos UTF-8 e arquivos antigos do Excel;
- conferência das linhas antes de salvar qualquer cliente;
- indicação de linhas prontas, inválidas e duplicadas;
- bloqueio de CPF já cadastrado ou repetido no próprio arquivo;
- importação somente das linhas válidas após confirmação;
- limite de 500 clientes e 2 MB por arquivo;
- atualização automática da lista de clientes após a importação;
- registro da operação no **Histórico de atividades**.

## Arquivos que devem ser substituídos

Substitua somente estes cinco arquivos no repositório `csadvogados/cs-platform`:

1. `backend/app/api/routes/clients.py`
2. `backend/app/schemas/client.py`
3. `frontend/index.html`
4. `frontend/assets/app.js`
5. `frontend/assets/styles.css`

Os arquivos já estão nas pastas corretas dentro deste ZIP.

## Aplicação pelo GitHub

1. Extraia este ZIP no computador.
2. Abra o repositório `csadvogados/cs-platform` no GitHub.
3. Substitua os cinco arquivos acima, mantendo exatamente os mesmos caminhos.
4. Faça todos os arquivos no mesmo commit.
5. Use este nome no commit:

   `feat: adicionar importação de clientes por CSV v5.7.3`

6. Confirme o commit na branch `main`.
7. Aguarde o Railway concluir os deployments de `cs-platform-api` e `cs-platform-web`.

## Não altere no Railway

Esta versão não exige:

- migration do banco de dados;
- variável nova;
- mudança em `railway.json`;
- mudança em `Dockerfile`;
- comando manual no Console.

## Como preparar o CSV

As colunas obrigatórias são:

- `Nome`
- `CPF`

As demais colunas são opcionais. O modo mais simples é abrir **Clientes**, clicar em **Exportar CSV**, editar uma cópia desse arquivo no Excel e depois importá-la.

O sistema também reconhece: Nascimento, Profissão, E-mail, Telefone, Cidade, Estado, Status, Pessoa natural, Boa-fé declarada, Capacidade de pagamento e Observações.

## Teste depois do deployment

1. Abra `https://cs-platform-web-production.up.railway.app/`.
2. Pressione `Ctrl + F5`.
3. Entre com uma conta de administrador ou supervisor.
4. Clique em **Clientes**.
5. Clique em **Importar CSV**.
6. Selecione um arquivo `.csv` com as colunas Nome e CPF.
7. Clique em **Conferir arquivo**.
8. Confira os totais de linhas prontas, inválidas e duplicadas.
9. Clique em **Importar clientes**.
10. Confirme que os clientes válidos apareceram na lista.
11. Abra **Histórico** e confira a atividade **Importou — Cliente**.

Linhas inválidas ou duplicadas não são salvas. Se um CPF for cadastrado por outra pessoa entre a conferência e a confirmação, toda a gravação é interrompida para evitar importação parcial incorreta.

## Validações realizadas

- sintaxe Python e JavaScript;
- leitura de CSV com `;` e `,`;
- codificações UTF-8 com BOM e Windows-1252;
- acentos, datas brasileiras e campos Sim/Não;
- limite de tamanho e quantidade de linhas;
- colunas obrigatórias Nome e CPF;
- CPF inválido, repetido no arquivo e já cadastrado;
- isolamento por organização;
- permissões de criação e exportação de clientes;
- ordem correta das rotas da API;
- fluxo real de seleção, prévia e confirmação em navegador local;
- confirmação de que apenas linhas válidas foram enviadas;
- estrutura e hashes SHA-256 do ZIP.
