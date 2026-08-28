# CS Platform v5.16.0 — Gestão de carga da equipe

Esta versão amplia a central de cobranças com uma visão da carga de trabalho e distribuição equilibrada entre os responsáveis.

## Novidades

- painel de carga por responsável;
- totais de cobranças abertas, atrasadas e urgentes por pessoa;
- valor financeiro em aberto por responsável;
- atalho **Ver fila** para filtrar as cobranças de uma pessoa;
- distribuição equilibrada de duas ou mais cobranças entre dois ou mais usuários ativos;
- distribuição iniciada pelo responsável com a menor carga atual;
- opção de manter ou alterar a prioridade durante a distribuição;
- atualização automática da fila e dos totais após a confirmação;
- registro individual de cada mudança no histórico de atividades;
- acesso à distribuição restrito a administradores e supervisores.

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

`feat: adicionar gestão de carga e distribuição de cobranças v5.16.0`

## Teste após o deploy

1. Aguarde os deployments da API e da interface ficarem verdes.
2. Abra o sistema e pressione `Ctrl + F5`.
3. Entre com uma conta de administrador ou supervisor e abra **Cobranças**.
4. Expanda **Carga da equipe** e confira os totais de cada responsável.
5. Marque pelo menos duas cobranças abertas.
6. Clique em **Distribuir selecionadas**.
7. Mantenha pelo menos dois responsáveis marcados e confirme.
8. Confira se as cobranças foram divididas e se o painel de carga foi atualizado.
9. Clique em **Ver fila** ao lado de um responsável e confirme o filtro.
10. Verifique no **Histórico** que cada alteração foi registrada.

Cobranças pagas ou canceladas não participam da distribuição.

## Validações realizadas

- sintaxe de todos os arquivos Python;
- sintaxe do JavaScript;
- cadeia de migrações existente, sem nova migration;
- abertura e confirmação da janela de distribuição;
- divisão equilibrada entre dois responsáveis;
- atualização automática do painel de carga;
- filtro da fila por responsável;
- preservação de cobranças pagas;
- validação estrutural do pacote.
