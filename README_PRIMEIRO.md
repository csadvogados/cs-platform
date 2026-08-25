# CS Platform v5.9.0 — Controle de parcelas e pagamentos

Este pacote atualiza a versão v5.8.0 já instalada. Ele não apaga clientes, dívidas, acordos ou outros dados existentes.

## O que foi adicionado

- geração automática das parcelas ao cadastrar um acordo;
- geração de parcelas para acordos antigos que ainda não possuem grade;
- situações **Pendente**, **Paga**, **Atrasada** e **Cancelada**;
- registro de valor, data, forma e observação do pagamento;
- estorno de pagamento;
- cálculo automático do total recebido e do saldo restante;
- conclusão automática do acordo quando todas as parcelas forem pagas;
- histórico das operações na auditoria;
- proteção contra alteração ou exclusão de acordo com pagamentos registrados.

## Arquivos que devem ser substituídos

Copie os 10 arquivos abaixo para os mesmos caminhos do repositório no GitHub:

1. `backend/alembic/versions/0010_payment_installments.py` — arquivo novo
2. `backend/app/api/routes/financial.py`
3. `backend/app/core/constants.py`
4. `backend/app/models/__init__.py`
5. `backend/app/models/financial.py`
6. `backend/app/schemas/financial.py`
7. `backend/docker-entrypoint.sh`
8. `frontend/index.html`
9. `frontend/assets/app.js`
10. `frontend/assets/styles.css`

Não apague a migração anterior `0009_payment_agreements.py`.

## Nome sugerido para o commit

`feat: adicionar controle de parcelas e pagamentos v5.9.0`

## Deploy

Depois do commit, aguarde o Railway concluir os dois serviços:

- `cs-platform-api`;
- `cs-platform-web`.

A API executará automaticamente a migração `0010_payment_installments` durante a inicialização. Não coloque comando adicional em **Pre-deploy Command**.

## Teste após o deploy

1. Abra a plataforma e pressione `Ctrl + F5`.
2. Entre em **Clientes** e abra **Ver detalhes**.
3. Cadastre um novo acordo com 2 parcelas.
4. Confirme que as duas parcelas aparecem com seus vencimentos.
5. Na primeira parcela, clique em **Registrar pagamento**.
6. Confirme que ela muda para **Paga**, o total recebido aumenta e o saldo restante diminui.
7. Clique em **Estornar** e confirme que a parcela volta para **Pendente** ou **Atrasada**.

Para um acordo criado na v5.8.0, clique em **Gerar parcelas** uma única vez.
