# CS Platform v5.6.2 — edição financeira

Este pacote mantém as correções financeiras da v5.6.1 e acrescenta o botão **Editar** em:

- receitas;
- despesas;
- dívidas.

Ao salvar uma alteração, os totais e a prévia do diagnóstico são recarregados automaticamente. A edição respeita o cliente, a organização e as permissões do usuário conectado.

## Como aplicar no GitHub

Substitua exatamente estes cinco arquivos no repositório `csadvogados/cs-platform`:

1. `backend/app/api/routes/financial.py`
2. `backend/app/services/diagnosis_engine.py`
3. `frontend/index.html`
4. `frontend/assets/app.js`
5. `frontend/assets/styles.css`

Use este nome no commit:

`feat: adicionar edição financeira v5.6.2`

O commit deverá gerar dois deployments no Railway:

- `cs-platform-api`;
- `cs-platform-web`.

Aguarde os dois ficarem verdes. Depois, abra o sistema e pressione `Ctrl + F5`.

Não altere banco, migrations, variáveis, `railway.json`, `Dockerfile`, `docker-entrypoint.sh` ou `nginx.conf`. Esta versão não exige migration.

## Teste depois do deploy

1. Entre em **Clientes** e clique em **Ver detalhes**.
2. Em uma receita, clique em **Editar**, altere o valor e salve.
3. Confirme que o total de receitas e a prévia do diagnóstico mudaram.
4. Repita o teste em uma despesa.
5. Repita o teste em uma dívida, alterando a parcela mensal.
6. Confira se os botões **Apagar** continuam funcionando.
7. Se os dados estiverem corretos, clique em **Salvar diagnóstico** para registrar uma nova versão.

Os diagnósticos já salvos permanecem no histórico.

## Conferência

O arquivo `SHA256SUMS.txt` contém os códigos SHA-256 dos cinco arquivos do patch.
