# CS Platform v5.13.0 — Relatórios de cobrança

Esta versão acrescenta gestão de resultados à Central de cobranças, mantendo todos os recursos já validados na v5.12.0.

## Novidades

- relatório por período, inicialmente preenchido com o mês atual;
- valores vencidos e recebidos no período;
- índice de recebimento, calculado sobre os vencimentos do período;
- total atual de parcelas atrasadas;
- ações, clientes contatados e promessas registradas;
- quadro de atuação por responsável;
- exportação do relatório em CSV;
- registro da exportação no Histórico de atividades.

Não existe migração nova nesta versão. A migração mais recente continua sendo `0012_action_cancellation`.

## Arquivos que devem ser substituídos

1. `backend/app/api/routes/financial.py`
2. `backend/app/core/constants.py`
3. `backend/app/schemas/financial.py`
4. `backend/docker-entrypoint.sh`
5. `frontend/index.html`
6. `frontend/assets/app.js`
7. `frontend/assets/styles.css`

Use no commit:

`feat: adicionar relatórios gerenciais de cobrança v5.13.0`

Após os deployments da API e da Web ficarem verdes, abra o sistema e pressione `Ctrl + F5`.

## Teste recomendado

1. Abra **Cobranças**.
2. Localize o novo quadro **Relatório gerencial de cobranças**.
3. Confirme que o período começa no primeiro dia do mês e termina na data atual.
4. Altere as datas e clique em **Atualizar relatório**.
5. Confira os valores, ações, promessas e o quadro da equipe.
6. Clique em **Exportar CSV** e abra o arquivo baixado.
7. No menu **Histórico**, confirme o registro da exportação.
