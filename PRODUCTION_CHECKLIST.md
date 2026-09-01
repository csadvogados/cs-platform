# CS Platform — Checklist de produção

## Antes do deploy

- Confirmar que o deploy usa a branch `staging-cs-recupera` e que API, web e PostgreSQL apontam para o mesmo ambiente.
- Fazer backup do banco PostgreSQL e validar que ele pode ser restaurado.
- Conferir as variáveis obrigatórias: `DATABASE_URL` PostgreSQL, `SECRET_KEY` exclusiva com 32+ caracteres, `INITIAL_ADMIN_PASSWORD` exclusiva com 12+ caracteres e origens CORS sem `*`.
- Manter `RESET_ADMIN_ON_STARTUP=false`. Se métricas forem coletadas, configurar `METRICS_TOKEN` e enviar `Authorization: Bearer <token>`; sem token, `/metrics` permanece indisponível em produção.
- Executar todos os testes automatizados e confirmar apenas uma cabeça Alembic: `0024`.

## Deploy

- Publicar primeiro a API. O inicializador aplicará as migrations pendentes até `0024`.
- Confirmar `/api/v1/health`, `/ping` e os logs de inicialização sem erros.
- Publicar a interface web e confirmar que ela está usando a versão `5.40.0-judicial-dossier`.
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

## Backup e restauração no Railway

- Habilitar backups automáticos no serviço PostgreSQL do ambiente de produção e confirmar a política de retenção exibida pelo Railway.
- Antes de cada deploy com migration, criar um backup manual e registrar data, responsável e migration atual.
- Mensalmente, restaurar o backup mais recente em um banco temporário isolado; nunca sobre o banco de produção.
- No banco restaurado, confirmar a revisão Alembic, a quantidade de organizações/clientes/processos e uma amostra de documentos e auditorias.
- Registrar o resultado do teste, o tempo de restauração e apagar o banco temporário somente depois da validação.

## Auditoria e resposta a incidentes

- Semanalmente, revisar em **Histórico** tentativas de login, redefinições de senha, alterações de usuários, exportações e encerramentos judiciais.
- Em suspeita de acesso indevido: bloquear o usuário, redefinir a senha, revogar sessões, preservar os logs e registrar o intervalo do incidente.
- Nunca inserir senhas, tokens, chaves ou documentos integrais em tickets e capturas de tela.
