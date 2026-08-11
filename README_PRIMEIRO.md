# CS Platform v5.6.5 — relatório do diagnóstico

Este pacote acrescenta relatórios profissionais, prontos para impressão ou para salvar em PDF.

Existem dois tipos de relatório:

- **Relatório atual:** usa os dados financeiros existentes no momento da abertura;
- **Relatório de uma versão salva:** reproduz os valores, a pontuação, a conclusão e os alertas registrados naquela versão do histórico.

O relatório inclui identidade da CS Platform, cliente e CPF, valores em formato brasileiro, comprometimento, pontuação, conclusão, alertas, aviso técnico e campos de assinatura.

## Como aplicar no GitHub

Substitua exatamente estes cinco arquivos no repositório `csadvogados/cs-platform`:

1. `backend/app/api/routes/diagnoses.py`
2. `backend/app/services/report_service.py`
3. `frontend/index.html`
4. `frontend/assets/app.js`
5. `frontend/assets/styles.css`

Use este nome no commit:

`feat: adicionar relatório imprimível v5.6.5`

O commit deverá gerar dois deployments no Railway:

- `cs-platform-api`;
- `cs-platform-web`.

Aguarde os dois ficarem verdes. Depois, abra o sistema e pressione `Ctrl + F5`.

Não altere banco, migrations, variáveis, `railway.json`, `Dockerfile`, `docker-entrypoint.sh` ou `nginx.conf`. Esta versão não exige migration.

## Teste depois do deploy

1. Entre em **Clientes** e clique em **Ver detalhes**.
2. Na área **Diagnóstico financeiro**, clique em **Abrir relatório**.
3. Se o navegador bloquear a janela, autorize pop-ups para o endereço do sistema e tente novamente.
4. No relatório, clique em **Imprimir / Salvar como PDF**.
5. Na janela de impressão, selecione **Salvar como PDF**.
6. Volte ao sistema e abra uma versão em **Histórico de diagnósticos**.
7. Clique em **Abrir relatório desta versão** e confirme se o número da versão e os valores estão corretos.

O acesso continua autenticado. O token não é colocado no endereço do relatório.

## Conferência

O arquivo `SHA256SUMS.txt` contém os códigos SHA-256 dos cinco arquivos substituídos.
