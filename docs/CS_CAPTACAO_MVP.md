# CS Captação / CRM — MVP

Módulo transversal do core comercial. O cadastro de lead é separado de Cliente; a conversão preserva o histórico comercial e pode abrir um `RecoveryCase` quando o serviço é `CS_RECUPERA`.

## Banco e migration

Aplicar com `alembic upgrade head`. A revision `0025_cs_captacao_mvp` cria `lead_sources`, `service_types`, `leads`, `lead_interactions`, `lead_tasks` e `lead_proposals`, incluindo índices multitenant, auditoria por serviço e exclusão lógica.

Os catálogos padronizados são criados por organização no primeiro acesso a `GET /api/v1/leads/catalogs`.

## API

- `GET/POST /api/v1/leads`
- `GET/PATCH/DELETE /api/v1/leads/{id}`
- `POST /api/v1/leads/{id}/status`
- `GET /api/v1/leads/{id}/timeline`
- `POST /api/v1/leads/{id}/interactions`
- `POST /api/v1/leads/{id}/tasks`
- `PATCH /api/v1/leads/{id}/tasks/{task_id}/complete`
- `POST /api/v1/leads/{id}/proposals`
- `POST /api/v1/leads/{id}/convert`
- `GET /api/v1/leads/catalogs`
- `GET /api/v1/leads/analytics/dashboard`
- `GET /api/v1/leads/analytics/reports`

Todos aparecem no Swagger na tag **CS Captação / Leads** e são isolados por organização. Administrador, supervisor, advogado e atendimento têm acesso; os demais perfis recebem 403.

## Regras principais

- Ao menos um meio de contato é obrigatório.
- Mover para `PERDIDO` exige motivo.
- A conversão pesquisa duplicidade por CPF, telefone e e-mail.
- Como `Client.cpf` é obrigatório no core atual, um lead sem CPF pode avançar no funil, mas precisa de CPF para criar um novo Cliente. Pode, porém, ser vinculado a um Cliente existente após a confirmação de duplicidade.
- `RecoveryCase` só é aberto para o serviço `CS_RECUPERA`.
- Exclusão de lead é lógica e auditada.

## Teste local

1. No backend, aplique `alembic upgrade head`.
2. Execute `python -m pytest -q`.
3. Inicie API e frontend como descrito no README principal.
4. Entre com um usuário permitido e abra **CS Captação** no menu CRM.
5. Cadastre um lead, mova-o no funil, registre interação/proposta e converta-o.

## Fora do escopo

Chatbot, marketing automatizado, Meta/Google Ads, scraping, IA, landing pages, assinatura/cobrança automáticas e call center não foram incluídos.
