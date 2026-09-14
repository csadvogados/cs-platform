# Auditoria — CS Captação / CRM MVP — v5.5.0

## Base auditada

Snapshot-base: **CS Platform v5.4.2 Revisada — Infrastructure & Deployment**.

A base já possuía CRM Enterprise v5.4.0 e estabilização v5.4.1, com contatos, interações, oportunidades, tarefas, summary, isolamento por organização e migrations 0005/0006.

## Resultado da auditoria antes da continuação manual

| Requisito | Estado encontrado | Observação |
|---|---|---|
| Tabelas CRM básicas | PRONTO | `crm_contacts`, `crm_interactions`, `crm_opportunities`, `crm_tasks`. |
| Migrations 0005/0006 | PRONTO | CRM Enterprise e estabilização/índices. |
| CRUD CRM básico | PRONTO | Contatos, interações, oportunidades e tarefas. |
| Funil aprovado do CS Captação | PARCIAL | Base usava `lead/qualified/proposal/negotiation/won/lost`. |
| Origem do lead | FALTANDO | Sem `source` na oportunidade. |
| Serviço de interesse | FALTANDO | Sem `service` na oportunidade. |
| Próximo contato | FALTANDO | Sem `next_contact_at`. |
| Histórico de mudança de etapa | FALTANDO | Não havia entidade própria de histórico. |
| Auditoria completa do CRM | PARCIAL | Criação de contato possuía auditoria explícita; demais mutações não estavam completas. |
| RBAC específico do CRM | FALTANDO | Rotas dependiam essencialmente de autenticação, sem permissões CRM próprias. |
| Pipeline/Kanban — API | FALTANDO | Não havia endpoint próprio por colunas/cartões. |
| Detalhe do lead — API | FALTANDO | Não havia agregação de cliente + oportunidade + interações + tarefas + histórico. |
| Lead → Cliente | PARCIAL | `Client` já era a identidade canônica desde o estágio `lead`, mas faltava a conversão comercial formal. |
| Cliente → Caso CS Recupera | FALTANDO | Não havia entidade `Case` nem conversão automática. |
| Dashboard de Captação | PARCIAL | Existia apenas summary genérico do CRM. |
| Filtros por origem/serviço/responsável/período | PARCIAL | Alguns filtros genéricos; não o conjunto do MVP. |
| Testes CRM | PARCIAL | Cobriam o CRM genérico v5.4.0/v5.4.1. |
| Frontend Kanban/Detalhe/Dashboard | FALTANDO NO SNAPSHOT | O pacote auditado não contém código frontend. |
| Relatórios de captação/exportação dedicados | PENDENTE | Não havia módulo de relatório/exportação específico do CS Captação. |

## Continuação manual implementada na v5.5.0

### Funil oficial

`NOVO → CONTATADO → QUALIFICADO → PROPOSTA → CONVERTIDO / PERDIDO`

Valores técnicos:

- `new`
- `contacted`
- `qualified`
- `proposal`
- `converted`
- `lost`

A migration converte dados legados:

- `lead` → `new`
- `negotiation` → `proposal`
- `won` → `converted`

### Dados comerciais adicionados

Em `crm_opportunities`:

- `source`
- `service`
- `next_contact_at`
- `stage_changed_at`
- `converted_at`
- `lost_at`
- `lost_reason`

### Histórico do funil

Nova tabela `crm_opportunity_stage_history`, contendo:

- organização;
- oportunidade;
- usuário responsável pela mudança;
- etapa anterior;
- nova etapa;
- observação;
- data/hora da alteração.

### Conversão

A arquitetura preserva **uma única identidade de cliente**: o registro em `clients` existe desde a captação e passa de `lead` para `contracted` na conversão.

Para oportunidade cujo serviço contenha **CS Recupera**, a conversão pode criar automaticamente um registro em `cases`, vinculado a:

- organização;
- cliente;
- oportunidade;
- responsável;
- serviço;
- status inicial.

A criação é idempotente por oportunidade.

### Permissões CRM

Adicionadas:

- `crm.create`
- `crm.read`
- `crm.update`
- `crm.delete`
- `crm.convert`

As permissões foram distribuídas nos perfis padrão, preservando acesso total do administrador e níveis compatíveis para supervisor, advogado, negociador, financeiro, atendimento e consulta.

### Auditoria

`audit_events` passa a armazenar também `old_values`, permitindo registrar valor anterior e posterior.

Mutações de contatos, interações, oportunidades, etapas, tarefas, conversão e criação de caso passam a gerar eventos de auditoria apropriados.

### Endpoints adicionados/expandidos

- `GET /api/v1/crm/pipeline`
- `GET /api/v1/crm/dashboard`
- `GET /api/v1/crm/opportunities/{id}/detail`
- `POST /api/v1/crm/opportunities/{id}/stage`
- `GET /api/v1/crm/opportunities/{id}/history`
- `POST /api/v1/crm/opportunities/{id}/convert`

`GET /api/v1/crm/opportunities` passa a aceitar filtros de responsável, origem, serviço e período, além dos filtros anteriores.

### Dashboard do MVP

Disponibiliza:

- leads novos;
- leads em andamento;
- leads qualificados;
- propostas abertas;
- leads convertidos;
- leads perdidos;
- taxa de conversão;
- tempo médio até conversão;
- receita estimada das propostas;
- receita contratada;
- follow-ups vencidos.

Filtros: período, responsável, origem e serviço.

## Validação executada

- `python -m compileall -q app alembic tests`: **OK**.
- criação integral do schema SQLAlchemy em banco SQLite limpo: **OK**.
- `alembic heads`: **0007_cs_captacao_mvp (head)**.
- suíte automatizada completa: **48 testes aprovados**.

Para executar a suíte no ambiente de auditoria foi usado apenas um adaptador temporário de `pwdlib` sobre Argon2 porque a biblioteca `pwdlib` não estava instalada no container da auditoria. Esse adaptador não integra o pacote entregue. No ambiente normal, `requirements.txt` continua sendo a fonte de dependências.

## Pendências reais após v5.5.0

1. **Frontend:** implementar Kanban, cadastro/edição comercial, detalhe do lead, dashboard e drag-and-drop consumindo a API pronta.
2. **Relatórios de captação:** definir e implementar tela/exportação dedicada caso permaneça no escopo do MVP final.
3. **Homologação PostgreSQL/Railway:** executar migration 0007 em ambiente de homologação, smoke test da API e somente depois produção.

## Conclusão

O backend do CS Captação deixa de ser um CRM genérico e passa a cobrir o núcleo operacional do MVP: captação, funil, acompanhamento, histórico, tarefas, auditoria, conversão e criação do caso CS Recupera. O maior bloco ainda ausente no snapshot é o frontend.
