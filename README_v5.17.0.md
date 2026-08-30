# CS Platform v5.17.0 — Envelhecimento da inadimplência

Esta versão acrescenta uma visão gerencial das cobranças atrasadas por tempo de inadimplência.

## Novidades

- painel **Envelhecimento da inadimplência** na central de cobranças;
- faixas de atraso de **1 a 7 dias**, **8 a 30 dias**, **31 a 60 dias** e **mais de 60 dias**;
- quantidade e valor financeiro acumulado em cada faixa;
- cartões clicáveis que abrem diretamente a fila correspondente;
- novo filtro **Tempo de atraso**;
- destaque visual da faixa selecionada;
- mensagem informando quantas cobranças foram encontradas;
- botão **Limpar** restaura todas as faixas e cobranças;
- preservação da gestão de carga e distribuição equilibrada da v5.16.1.

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

`feat: adicionar faixas de atraso nas cobranças v5.17.0`

## Teste após o deploy

1. Abra **Cobranças**.
2. Confira o painel **Envelhecimento da inadimplência**.
3. Verifique a quantidade e o valor de cada faixa.
4. Clique em uma faixa que possua cobranças.
5. Confirme que a fila foi filtrada e que a faixa ficou destacada.
6. Clique em uma faixa vazia e confirme a indicação de zero cobranças.
7. Clique em **Limpar** e confirme o retorno de todas as cobranças.

## Validações realizadas

- limites de 1, 7, 8, 30, 31, 60 e 61 dias;
- cálculo das quatro faixas;
- filtro integrado à API;
- cartões, destaque e mensagem na interface;
- retorno de faixa vazia;
- limpeza dos filtros;
- sintaxe Python e JavaScript;
- cadeia de migrações existente, sem nova migration.
