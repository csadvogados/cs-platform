# CS Platform — Checklist de produção

## Antes do deploy

- Confirmar que o deploy usa a branch `staging-cs-recupera` e que API, web e PostgreSQL apontam para o mesmo ambiente.
- Fazer backup do banco PostgreSQL e validar que ele pode ser restaurado.
- Conferir as variáveis obrigatórias: `DATABASE_URL`, `SECRET_KEY`, origens CORS e credenciais administrativas iniciais.
- Executar todos os testes automatizados e confirmar apenas uma cabeça Alembic: `0024`.

## Deploy

- Publicar primeiro a API. O inicializador aplicará as migrations pendentes até `0024`.
- Confirmar `/api/v1/health`, `/ping` e os logs de inicialização sem erros.
- Publicar a interface web e confirmar que ela está usando a versão `5.37.0-production-ready`.
- Entrar com um administrador e atualizar a página sem usar conteúdo antigo do navegador.

## Teste rápido após o deploy

- Criar e arquivar/restaurar um cliente.
- Abrir um caso, avançar o fluxo e consultar o processo judicial.
- Registrar uma movimentação e um prazo; conferir Agenda e Notificações.
- Concluir o prazo e conferir sua remoção da agenda.
- Encerrar um processo com resultado e verificar que ele não aceita novas alterações.
- Abrir o relatório judicial, filtrar datas e exportar CSV.
- Entrar com Atendimento/Financeiro e confirmar que ações judiciais restritas não aparecem nem são aceitas pela API.

## Rollback

- Em falha apenas da interface, restaurar o último deploy web estável; a API permanece compatível.
- Em falha da API, restaurar o deploy anterior e o backup feito antes da publicação.
- Não reverter migrations em produção sem backup confirmado e análise dos dados incluídos depois do deploy.
- Registrar horário, serviço afetado, versão restaurada e resultado do teste de saúde.
