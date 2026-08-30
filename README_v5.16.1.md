# CS Platform v5.16.1 — Correção do botão Ver fila

Esta versão corrige e melhora o retorno visual do botão **Ver fila** no painel de carga da equipe.

## Correções

- o responsável escolhido passa a aparecer imediatamente no filtro;
- a página rola automaticamente até a lista de cobranças;
- uma mensagem informa qual fila foi aberta e quantas cobranças foram encontradas;
- filas vazias exibem claramente `0 cobranças`;
- permanecem todos os recursos de carga e distribuição equilibrada da v5.16.0.

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

`fix: corrigir filtro Ver fila v5.16.1`

## Teste após o deploy

1. Abra **Cobranças**.
2. Expanda **Carga da equipe**.
3. Clique em **Ver fila** ao lado de um responsável.
4. Confirme que a tela desce até os filtros.
5. Confirme que o responsável aparece selecionado.
6. Confira a mensagem com a quantidade de cobranças encontradas.
