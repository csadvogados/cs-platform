# CS Platform v5.6.8 — busca e filtros no CRM

Este pacote acrescenta ferramentas para localizar registros rapidamente quando a base do CRM crescer.

Ele permite:

- pesquisar simultaneamente oportunidades, tarefas, contatos e atendimentos;
- encontrar registros pelo nome do cliente, título, assunto, descrição, contato ou etapa;
- filtrar tarefas por status;
- filtrar tarefas por prioridade;
- filtrar atendimentos por tipo;
- combinar busca e filtros;
- manter os filtros após clicar em **Atualizar**;
- restaurar todos os registros com **Limpar filtros**;
- exibir a quantidade de registros encontrados e o total disponível.

## Como aplicar no GitHub

Substitua exatamente estes três arquivos no repositório `csadvogados/cs-platform`:

1. `frontend/index.html`
2. `frontend/assets/app.js`
3. `frontend/assets/styles.css`

Use este nome no commit:

`feat: adicionar busca e filtros no CRM v5.6.8`

O commit deverá gerar o deployment do serviço `cs-platform-web` no Railway. Se a API aparecer como **Skipped / No changes to watched files**, isso é normal.

Aguarde o `cs-platform-web` ficar verde. Depois, abra o sistema e pressione `Ctrl + F5`.

Não altere banco, migrations, variáveis, `railway.json`, `Dockerfile`, `docker-entrypoint.sh` ou `nginx.conf`. Esta versão não exige migration.

## Teste depois do deploy

1. Entre em **CRM**.
2. No campo **Buscar no CRM**, digite o nome de um cliente existente.
3. Abra as abas e confirme que somente os registros relacionados aparecem.
4. Apague a busca e selecione um **Status da tarefa**.
5. Combine o status com uma **Prioridade**.
6. Selecione um **Tipo de atendimento**.
7. Clique em **Atualizar** e confirme que os filtros permanecem selecionados.
8. Clique em **Limpar filtros** e confirme que todos os registros retornam.

## Conferência

O arquivo `SHA256SUMS.txt` contém os códigos SHA-256 dos três arquivos substituídos.
