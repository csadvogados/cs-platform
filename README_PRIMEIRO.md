# CS Platform v5.6.7 — histórico de atendimentos

Este pacote acrescenta uma nova aba **Atendimentos** ao CRM.

Ela permite:

- registrar ligação, e-mail, reunião, mensagem, observação ou outro atendimento;
- vincular obrigatoriamente o atendimento a um cliente;
- informar data, horário, assunto e descrição;
- visualizar os registros mais recentes primeiro;
- apagar registros de teste com confirmação;
- atualizar automaticamente a quantidade exibida no histórico.

## Como aplicar no GitHub

Substitua exatamente estes três arquivos no repositório `csadvogados/cs-platform`:

1. `frontend/index.html`
2. `frontend/assets/app.js`
3. `frontend/assets/styles.css`

Use este nome no commit:

`feat: adicionar histórico de atendimentos v5.6.7`

O commit deverá gerar o deployment do serviço `cs-platform-web` no Railway. Se o serviço da API aparecer como **Skipped / No changes to watched files**, isso é normal.

Aguarde o `cs-platform-web` ficar verde. Depois, abra o sistema e pressione `Ctrl + F5`.

Não altere banco, migrations, variáveis, `railway.json`, `Dockerfile`, `docker-entrypoint.sh` ou `nginx.conf`. A API atual já possui as rotas necessárias e esta versão não exige migration.

## Teste depois do deploy

1. Entre em **CRM** e abra a aba **Atendimentos**.
2. Clique em **Novo atendimento**.
3. Selecione um cliente e o tipo de atendimento.
4. Preencha o assunto e, se desejar, a descrição.
5. Confirme se a data e o horário já aparecem preenchidos e salve.
6. Verifique se o registro aparece no topo do histórico.
7. Crie um registro de teste, clique em **Apagar** e confirme a exclusão.
8. Abra novamente o formulário e confirme que o botão **X** fecha normalmente.

## Conferência

O arquivo `SHA256SUMS.txt` contém os códigos SHA-256 dos três arquivos substituídos.
