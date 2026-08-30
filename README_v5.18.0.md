# CS Platform v5.18.0 — Fila inteligente de cobranças

Esta versão transforma os dados da central de cobranças em uma fila de trabalho priorizada.

## Novidades

- classificação das cobranças como **Crítica**, **Exige atenção** ou **Rotina**;
- pontuação calculada a partir do atraso, prioridade, promessa vencida, acompanhamento atrasado e ausência de responsável;
- ação recomendada para cada cobrança;
- quantidade de cobranças críticas e de atenção no resumo;
- filtro **Nível de atenção**;
- ordenação por **Ordem recomendada**, **Vencimento mais antigo** ou **Maior valor**;
- botão **Atender próxima**, que abre diretamente o registro de contato da primeira cobrança pendente da fila;
- indicação da quantidade de dias em atraso;
- preservação das faixas de atraso, distribuição equilibrada e histórico.

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

`feat: adicionar fila inteligente de cobranças v5.18.0`

## Teste após o deploy

1. Abra **Cobranças**.
2. Confira os indicadores de cobranças críticas e que exigem atenção.
3. Confira a nova coluna **Ação recomendada**.
4. Selecione **Crítica** no filtro **Nível de atenção** e aplique.
5. Teste as três opções de ordenação.
6. Escolha **Ordem recomendada**.
7. Clique em **Atender próxima**.
8. Confirme que abriu a janela para registrar contato da primeira cobrança pendente da fila.

## Validações realizadas

- cálculo de pontuação e níveis de atenção;
- precedência de promessa e acompanhamento vencidos;
- cobranças pagas sem ação pendente;
- filtro por nível de atenção;
- três formas de ordenação;
- abertura da cobrança prioritária;
- sintaxe Python e JavaScript;
- cadeia de migrações existente, sem nova migration.
