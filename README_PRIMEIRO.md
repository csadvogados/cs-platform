# CS Platform v5.7.1 — Histórico de atividades

Esta versão adiciona uma área protegida para consultar as atividades realizadas no sistema.

## O que foi incluído

- nova opção **Histórico** no menu;
- acesso restrito a administradores e supervisores;
- busca por pessoa, e-mail, área ou ação;
- filtros por área, ação, responsável e período;
- paginação com 25 atividades por página;
- registro de entrada, saída, alteração de senha e atualização da organização;
- registro ampliado de criações, alterações e exclusões no CRM e na ficha financeira;
- registro da criação de diagnósticos;
- proteção de senhas, tokens, hashes, CPF e CNPJ na resposta da API;
- separação dos dados por organização.

Não há migration nova. A tabela `audit_events` já existe no banco desde a migration `0001_sprint1`.

## Como aplicar no GitHub

Extraia o ZIP e substitua exatamente estes 11 arquivos no repositório `csadvogados/cs-platform`, mantendo as pastas:

1. `backend/app/api/routes/audit.py`
2. `backend/app/api/routes/auth.py`
3. `backend/app/api/routes/crm.py`
4. `backend/app/api/routes/diagnoses.py`
5. `backend/app/api/routes/financial.py`
6. `backend/app/api/routes/organizations.py`
7. `backend/app/main.py`
8. `backend/app/schemas/audit.py`
9. `frontend/index.html`
10. `frontend/assets/app.js`
11. `frontend/assets/styles.css`

Use este nome no commit:

`feat: adicionar histórico de atividades v5.7.1`

O commit deverá gerar dois deployments no Railway:

- `cs-platform-api`
- `cs-platform-web`

Aguarde os dois ficarem verdes. Depois, abra o sistema e pressione `Ctrl + F5`.

Não altere migrations, banco, variáveis, `railway.json`, `Dockerfile`, `docker-entrypoint.sh` ou `nginx.conf`.

## Como testar depois do deploy

1. Entre com uma conta de administrador.
2. Confira se apareceu **Histórico** no menu esquerdo.
3. Abra **Histórico** e confirme que as atividades existentes são exibidas da mais recente para a mais antiga.
4. Teste a busca pelo seu nome.
5. Teste os filtros **Área**, **Ação**, **Responsável**, **De** e **Até**.
6. Se houver mais de 25 registros, teste **Próxima página** e **Página anterior**.
7. Cadastre ou altere um registro no CRM, volte ao histórico e clique em **Atualizar**.
8. Entre com um perfil de atendimento, financeiro, negociador ou advogado e confirme que o menu **Histórico** não aparece.

Os eventos já gravados antes da v5.7.1 continuam disponíveis. A cobertura ampliada de CRM, financeiro, organização e diagnóstico começa após este deploy.

## Validações realizadas

- sintaxe de todos os arquivos Python;
- sintaxe do JavaScript;
- cadeia Alembic até `0008_add_client_payment_capacity`;
- presença da tabela `audit_events` na migration inicial;
- isolamento do histórico por organização;
- permissão `audit.read` para administrador e supervisor;
- busca, filtros, paginação e bloqueio de período inválido;
- ocultação do menu para perfil sem permissão;
- ausência de erros no console do navegador durante os testes.

O arquivo `SHA256SUMS.txt` contém os códigos SHA-256 dos 11 arquivos que devem ser substituídos.
