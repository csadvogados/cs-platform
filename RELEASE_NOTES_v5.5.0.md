# CS Platform v5.5.0 — CS Captação / CRM MVP

## Objetivo

Evoluir o CRM Enterprise v5.4.x para o fluxo comercial aprovado do **CS Captação**, preservando a arquitetura multi-tenant e a identidade única do cliente.

## Principais entregas

- funil `NOVO → CONTATADO → QUALIFICADO → PROPOSTA → CONVERTIDO/PERDIDO`;
- origem, serviço, próximo contato e motivo de perda na oportunidade;
- histórico persistente de mudanças do funil;
- pipeline pronto para Kanban;
- detalhe agregado do lead;
- dashboard de captação com filtros e KPIs;
- conversão de lead para cliente contratado;
- criação idempotente de caso **CS Recupera** na conversão;
- permissões próprias `crm.*`;
- auditoria com valores anteriores e posteriores;
- vínculo opcional de interação à oportunidade;
- migration Alembic `0007_cs_captacao_mvp`;
- testes funcionais do CS Captação.

## Compatibilidade de dados

A migration 0007 adapta etapas legadas:

- `lead` → `new`;
- `negotiation` → `proposal`;
- `won` → `converted`.

Não há exclusão destrutiva de leads, clientes ou oportunidades durante o upgrade.

## Qualidade

Validação manual desta entrega:

- compilação de app, migrations e testes: OK;
- criação de schema limpo: OK;
- Alembic head: `0007_cs_captacao_mvp`;
- suíte: **48 passed**.

## Fora desta entrega

O snapshot-base não contém frontend. Portanto, Kanban visual, detalhe visual e dashboard visual permanecem para a próxima etapa, consumindo os endpoints já disponibilizados.
