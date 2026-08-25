# CS Platform v5.10.0 — Agenda de cobranças

Este pacote deve ser aplicado sobre a versão v5.9.0 já instalada.

## Novidades

- nova opção **Cobranças** no menu principal;
- resumo de valores em aberto, atrasados, próximos do vencimento e recebidos no mês;
- identificação automática de parcelas que vencem nos próximos 7 dias;
- identificação automática de parcelas atrasadas;
- filtros por cliente ou acordo, situação e período de vencimento;
- acesso direto aos detalhes do cliente pela cobrança;
- alertas de cobranças no painel principal;
- atualização automática da agenda após registrar ou estornar um pagamento;
- proteção para que o pagamento corresponda ao valor integral da parcela.

## Arquivos que devem ser substituídos

Copie os 7 arquivos para os mesmos caminhos do repositório no GitHub:

1. `backend/app/api/routes/financial.py`
2. `backend/app/core/constants.py`
3. `backend/app/schemas/financial.py`
4. `backend/docker-entrypoint.sh`
5. `frontend/index.html`
6. `frontend/assets/app.js`
7. `frontend/assets/styles.css`

Esta versão não possui uma nova migração. Mantenha todas as migrações existentes, inclusive `0010_payment_installments.py`.

## Nome sugerido para o commit

`feat: adicionar agenda e alertas de cobranças v5.10.0`

## Deploy

Após o commit, aguarde o Railway concluir os deploys de:

- `cs-platform-api`;
- `cs-platform-web`.

Não adicione nenhum comando em **Pre-deploy Command**.

## Teste após o deploy

1. Abra a plataforma e pressione `Ctrl + F5`.
2. Confira no painel principal o bloco **Cobranças que exigem atenção**.
3. Entre em **Cobranças** pelo menu lateral.
4. Confirme os totais em aberto, atrasados, próximos de vencer e recebidos no mês.
5. Selecione o filtro **Atrasadas** e clique em **Aplicar filtros**.
6. Clique em **Abrir cliente** para conferir o acordo e suas parcelas.
