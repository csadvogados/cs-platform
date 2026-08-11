# CS Platform v5.6.4 — histórico de diagnósticos

Este pacote acrescenta o histórico dos diagnósticos salvos de cada cliente.

O histórico mostra:

- número da versão;
- data e hora em que foi salva;
- pontuação e resultado;
- renda, despesas, dívidas e parcelas;
- renda disponível e comprometimento;
- conclusão e alertas registrados naquela versão.

As versões aparecem da mais recente para a mais antiga. Ao salvar um novo diagnóstico, a nova versão aparece automaticamente no início do histórico. São exibidas até 50 versões por cliente.

## Como aplicar no GitHub

Substitua exatamente estes cinco arquivos no repositório `csadvogados/cs-platform`:

1. `backend/app/api/routes/diagnoses.py`
2. `backend/app/schemas/diagnosis.py`
3. `frontend/index.html`
4. `frontend/assets/app.js`
5. `frontend/assets/styles.css`

Use este nome no commit:

`feat: adicionar histórico de diagnósticos v5.6.4`

O commit deverá gerar dois deployments no Railway:

- `cs-platform-api`;
- `cs-platform-web`.

Aguarde os dois ficarem verdes. Depois, abra o sistema e pressione `Ctrl + F5`.

Não altere banco, migrations, variáveis, `railway.json`, `Dockerfile`, `docker-entrypoint.sh` ou `nginx.conf`. Esta versão não exige migration.

## Teste depois do deploy

1. Entre em **Clientes** e clique em **Ver detalhes**.
2. Role até **Histórico de diagnósticos**.
3. Confira se aparece pelo menos a versão salva anteriormente.
4. Clique em uma versão para abrir os valores, a conclusão e os alertas.
5. Clique em **Salvar diagnóstico**.
6. Confirme se uma nova versão aparece imediatamente no início do histórico.
7. Abra a versão anterior e confirme que seus valores não foram alterados.

## Conferência

O arquivo `SHA256SUMS.txt` contém os códigos SHA-256 dos cinco arquivos substituídos.
