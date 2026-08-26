# CS Platform v5.20.0 — LEIA PRIMEIRO

Este pacote adiciona a **Agenda operacional unificada**.

## Instalação

1. Substitua os sete arquivos do pacote no GitHub, mantendo as mesmas pastas.
2. Use o commit: `feat: adicionar agenda operacional unificada v5.20.0`.
3. Aguarde os deploys do `cs-platform-api` e do `cs-platform-web`.
4. Deixe o campo **Pre-deploy Command** vazio. Não há migração de banco.

## Teste

1. Atualize a plataforma com `Ctrl + F5` e entre normalmente.
2. Abra **Agenda** no menu lateral.
3. Confira os totais e a linha do tempo.
4. Teste os filtros de tipo, situação e período.
5. Clique em uma tarefa: o CRM deve abrir na aba Tarefas, com o registro localizado.
6. Clique em um acompanhamento ou promessa: Cobranças deve abrir com os filtros correspondentes.
7. Em Configurações, confirme a versão `5.20.0`.

## Arquivos

- `backend/app/api/routes/financial.py`
- `backend/app/core/constants.py`
- `backend/app/schemas/financial.py`
- `backend/docker-entrypoint.sh`
- `frontend/index.html`
- `frontend/assets/app.js`
- `frontend/assets/styles.css`
