# CS Platform v5.15.0 — Organização em massa da fila de cobranças

Esta versão permite organizar várias cobranças abertas ao mesmo tempo, preservando os recursos validados na v5.14.0.

## Novidades

- seleção individual de cobranças abertas;
- opção **Selecionar todas as cobranças visíveis**;
- contador de cobranças selecionadas;
- atribuição em massa de responsável;
- alteração em massa de prioridade;
- opções para manter o responsável ou a prioridade atual;
- cobranças pagas e canceladas não entram na seleção em massa;
- cada cobrança alterada continua registrada individualmente no histórico;
- organização em massa restrita a administradores e supervisores.

## Arquivos para substituir

1. `backend/app/api/routes/financial.py`
2. `backend/app/core/constants.py`
3. `backend/app/schemas/financial.py`
4. `backend/docker-entrypoint.sh`
5. `frontend/index.html`
6. `frontend/assets/app.js`
7. `frontend/assets/styles.css`

Não há nova migração de banco nesta versão.

## Commit sugerido

`feat: adicionar organização em massa de cobranças v5.15.0`

## Teste após o deploy

1. Abra **Cobranças**.
2. Marque duas cobranças abertas ou use **Selecionar todas as cobranças visíveis**.
3. Confira o contador de selecionadas.
4. Clique em **Organizar selecionadas**.
5. Escolha um responsável e a prioridade **Alta**.
6. Clique em **Aplicar organização**.
7. Confirme que todas as cobranças selecionadas exibem o responsável e a prioridade escolhidos.
8. Confirme que cobranças pagas não foram alteradas.
