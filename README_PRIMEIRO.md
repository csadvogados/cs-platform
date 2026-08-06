# CS Platform v5.6.1 — correção financeira

Este pacote corrige dois pontos da v5.6.0:

- reconhece corretamente as dívidas antigas cadastradas em português;
- adiciona exclusão de receitas, despesas e dívidas, sempre com confirmação.

Para os valores testados — renda de R$ 1.500, despesas de R$ 500 e parcelas de R$ 1.450 — a nova prévia reconhece duas dívidas de consumo, uma dívida de atenção específica e retorna 78 pontos: **Requer análise jurídica complementar**.

## Como aplicar no GitHub

Substitua exatamente estes cinco arquivos no repositório `csadvogados/cs-platform`:

1. `backend/app/api/routes/financial.py`
2. `backend/app/services/diagnosis_engine.py`
3. `frontend/index.html`
4. `frontend/assets/app.js`
5. `frontend/assets/styles.css`

Use este nome no commit:

`fix: corrigir diagnóstico e exclusão financeira v5.6.1`

O commit deverá gerar dois deployments no Railway:

- `cs-platform-api`
- `cs-platform-web`

Aguarde os dois ficarem verdes antes de testar. Depois, abra o sistema e pressione `Ctrl + F5`.

Não altere o banco, migrations, variáveis, `railway.json`, `Dockerfile` ou `nginx.conf`.

## Teste depois do deploy

1. Entre em **Clientes** e clique em **Ver detalhes**.
2. Na parte de diagnóstico, clique em **Atualizar prévia**.
3. Confira se a pontuação foi recalculada.
4. Confira os botões **Apagar** nas receitas, despesas e dívidas.
5. Clique em **Apagar** em um registro de teste e confirme a exclusão.
6. Confira se os totais e a prévia foram atualizados automaticamente.
7. Quando os dados estiverem corretos, clique em **Salvar diagnóstico** para criar uma nova versão.

Os diagnósticos já salvos permanecem no histórico; eles não são apagados automaticamente.

## Conferência

O arquivo `SHA256SUMS.txt` contém os códigos SHA-256 dos cinco arquivos substituídos.
