# CS Captação / CRM — MVP

Módulo transversal do core comercial. O cadastro de lead é separado de Cliente; a conversão preserva o histórico comercial e pode abrir um `RecoveryCase` quando o serviço é `CS_RECUPERA`.

## Banco e migration

Aplicar com `alembic upgrade head`. A revision `0025_cs_captacao_mvp` cria `lead_sources`, `service_types`, `leads`, `lead_interactions`, `lead_tasks` e `lead_proposals`, incluindo índices multitenant, auditoria por serviço e exclusão lógica.

Os catálogos padronizados são criados por organização no primeiro acesso a `GET /api/v1/leads/catalogs`.

## API

- `GET/POST /api/v1/leads`
- `GET/PATCH/DELETE /api/v1/leads/{id}`
- `GET /api/v1/leads/{id}/duplicates`
- `POST /api/v1/leads/{id}/status`
- `GET /api/v1/leads/{id}/timeline`
- `POST /api/v1/leads/{id}/interactions`
- `POST /api/v1/leads/{id}/tasks`
- `PATCH /api/v1/leads/{id}/tasks/{task_id}/complete`
- `POST /api/v1/leads/{id}/proposals`
- `PATCH /api/v1/leads/{id}/proposals/{proposal_id}`
- `POST /api/v1/leads/{id}/convert`
- `GET /api/v1/leads/catalogs`
- `GET /api/v1/leads/analytics/dashboard`
- `GET /api/v1/leads/analytics/reports`

Todos aparecem no Swagger na tag **CS Captação / Leads** e são isolados por organização. Administrador, supervisor, advogado e atendimento têm acesso; os demais perfis recebem 403.

## Regras principais

- Ao menos um meio de contato é obrigatório.
- Mover para `PERDIDO` exige motivo.
- A conversão pesquisa duplicidade por CPF, telefone e e-mail.
- Antes da conversão, a interface mostra cadastros coincidentes por CPF, telefone, WhatsApp ou e-mail e permite vincular o histórico ao cliente existente.
- O registro de perda usa motivos padronizados e legíveis; motivo e observações permanecem visíveis no detalhe do lead.
- Como `Client.cpf` é obrigatório no core atual, um lead sem CPF pode avançar no funil, mas precisa de CPF para criar um novo Cliente. Pode, porém, ser vinculado a um Cliente existente após a confirmação de duplicidade.
- `RecoveryCase` só é aberto para o serviço `CS_RECUPERA`.
- Exclusão de lead é lógica e auditada.

## Automação operacional

- A primeira interação real avança automaticamente o lead de `NOVO` para `CONTATADO`.
- A criação da primeira proposta avança o lead para `PROPOSTA`; propostas em aberto podem ser marcadas como aceitas ou recusadas pela timeline.
- Próximas ações com vencimento em até dois dias geram notificações internas; ações vencidas recebem prioridade crítica.
- Propostas enviadas ou em rascunho geram aviso quando faltam até três dias para a validade e mudam automaticamente para `EXPIRADA` após o vencimento.
- Leads ativos sem tarefa futura, parados há pelo menos três dias, geram aviso diário de acompanhamento.
- A preferência **somente itens atribuídos a mim** também restringe os alertas comerciais ao responsável pelo lead ou pela tarefa.
- Cada alerta abre diretamente o lead correspondente no funil. A timeline permite concluir a próxima ação sem sair do detalhe.
- O dashboard comercial exibe ações atrasadas, propostas vencendo e leads sem próxima ação.
- As mudanças automáticas de status e as conclusões de tarefas são auditadas. A sincronização usa chaves de deduplicação para não repetir o mesmo alerta.

As automações são sincronizadas quando a central de notificações é consultada, inclusive pelo sino de alertas da interface. Não há envio externo de mensagens nem execução de marketing.

## Teste local

1. No backend, aplique `alembic upgrade head`.
2. Execute `python -m pytest -q`.
3. Inicie API e frontend como descrito no README principal.
4. Entre com um usuário permitido e abra **CS Captação** no menu CRM.
5. Cadastre um lead, mova-o no funil, registre interação/proposta e converta-o.
6. Para validar automações, crie uma próxima ação com vencimento próximo e uma proposta com validade próxima; atualize o sino de notificações e confirme que **Abrir** leva ao detalhe do lead.

## Fora do escopo

Chatbot, marketing automatizado, Meta/Google Ads, scraping, IA, landing pages, assinatura/cobrança automáticas e call center não foram incluídos.
