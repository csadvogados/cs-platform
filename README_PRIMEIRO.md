# CS Platform v5.8.0 — Acordos e formas de pagamento

Este pacote deve ser aplicado sobre a **v5.7.6 já instalada**.

## O que esta versão acrescenta

- cadastro de acordos de pagamento dentro dos detalhes do cliente;
- vínculo opcional do acordo com uma dívida já cadastrada;
- formas de pagamento: Pix, boleto, transferência, dinheiro, cartões, débito automático e outra;
- valor original, valor negociado, entrada, quantidade e valor das parcelas;
- cálculo automático da parcela;
- primeiro vencimento e situação do acordo;
- edição e exclusão com confirmação;
- registro das operações no Histórico de atividades;
- correção de datas sem horário que podiam aparecer um dia antes;
- migration `0009_payment_agreements.py` aplicada automaticamente no deploy da API.

## Como instalar

1. Extraia este ZIP no computador.
2. Abra o repositório `csadvogados/cs-platform` no GitHub.
3. Copie os **10 arquivos** do pacote para o projeto, mantendo exatamente as mesmas pastas. Nove arquivos serão substituídos.
4. O décimo arquivo é novo e deve ser adicionado neste caminho:

   `backend/alembic/versions/0009_payment_agreements.py`

5. Faça um único commit com o nome:

   `feat: adicionar acordos e formas de pagamento v5.8.0`

6. Aguarde os dois deployments do Railway:

   - `cs-platform-api`
   - `cs-platform-web`

7. Não altere variáveis, comandos ou configurações do Railway. A migration será executada pelo `docker-entrypoint.sh` da API.

## Teste depois do deploy

1. Abra `https://cs-platform-api-production.up.railway.app/api/v1/health` e confirme:

   `{"status":"ok","database":"ok"}`

2. Entre em `https://cs-platform-web-production.up.railway.app/`.
3. Abra **Clientes** e depois **Ver detalhes** em um cliente que possua dívida.
4. Localize **Acordos de pagamento** e clique em **Novo acordo**.
5. Selecione a dívida. O título e o valor original devem ser preenchidos automaticamente.
6. Informe, para um teste simples:

   - forma: `Boleto`;
   - valor negociado: `7000`;
   - entrada: `1000`;
   - parcelas: `12`;
   - primeiro vencimento: uma data futura.

7. Clique em **Calcular parcela**. O resultado esperado é `12 parcela(s) de R$ 500`.
8. Clique em **Salvar acordo** e confirme que ele aparece na tabela.
9. Teste **Editar**, alterando a situação para **Concluído**.
10. Teste **Apagar** e confirme que o registro desaparece.

## Arquivos incluídos

- `backend/alembic/versions/0009_payment_agreements.py`
- `backend/app/api/routes/financial.py`
- `backend/app/core/constants.py`
- `backend/app/models/__init__.py`
- `backend/app/models/financial.py`
- `backend/app/schemas/financial.py`
- `backend/docker-entrypoint.sh`
- `frontend/index.html`
- `frontend/assets/app.js`
- `frontend/assets/styles.css`

Não copie `README_PRIMEIRO.md` nem `SHA256SUMS.txt` para o repositório; eles servem apenas como instrução e verificação do pacote.
