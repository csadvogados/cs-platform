# API — CS Captação / CRM MVP — v5.5.0

Base: `/api/v1/crm`

## Pipeline

`GET /pipeline`

Filtros: `owner_id`, `source`, `service`, `search`, `limit_per_stage`.

Retorna seis colunas: NEW, CONTACTED, QUALIFIED, PROPOSAL, CONVERTED e LOST, com cartões contendo cliente, telefone, serviço, origem, responsável, próximo contato e valor estimado.

## Oportunidades / Leads comerciais

- `GET /opportunities`
- `POST /opportunities`
- `GET /opportunities/{id}`
- `PATCH /opportunities/{id}`
- `DELETE /opportunities/{id}`
- `POST /opportunities/{id}/stage`
- `GET /opportunities/{id}/history`
- `GET /opportunities/{id}/detail`
- `POST /opportunities/{id}/convert`

Filtros da listagem: etapa, cliente, responsável, origem, serviço, pesquisa, data inicial e data final.

## Dashboard

`GET /dashboard`

Filtros: `date_from`, `date_to`, `owner_id`, `source`, `service`.

KPIs: novos, em andamento, qualificados, propostas, convertidos, perdidos, conversão, tempo médio, receita estimada, receita contratada e follow-ups vencidos.

## Interações

- `GET /interactions`
- `POST /interactions`
- `GET /interactions/{id}`
- `DELETE /interactions/{id}`

Uma interação pode ser vinculada diretamente à oportunidade por `opportunity_id`.

## Tarefas

- `GET /tasks`
- `POST /tasks`
- `GET /tasks/{id}`
- `PATCH /tasks/{id}`
- `POST /tasks/{id}/complete`
- `DELETE /tasks/{id}`

Ao receber somente `opportunity_id`, a API deriva o `client_id` da oportunidade.

## Contatos

- `GET /contacts`
- `POST /contacts`
- `GET /contacts/{id}`
- `PATCH /contacts/{id}`
- `DELETE /contacts/{id}`

## Permissões

As rotas exigem uma das permissões CRM conforme a operação:

- `crm.read`
- `crm.create`
- `crm.update`
- `crm.delete`
- `crm.convert`
