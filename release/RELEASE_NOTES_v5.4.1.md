# CS Platform v5.4.1 — CRM Stabilization

Release de estabilização construída sobre a v5.4.0.

## Entregas
- validação estrita dos estágios, prioridades, status e tipos de interação;
- validação multi-tenant de clientes, responsáveis e oportunidades relacionadas;
- CRUD ampliado para contatos, oportunidades e tarefas;
- exclusão de interações;
- filtros e paginação consistentes;
- tratamento de conflitos de persistência;
- indicadores de pipeline ponderado e tarefas vencidas;
- auditoria inicial da criação de contatos;
- cinco índices compostos para consultas críticas do CRM;
- testes de regressão e validação.

## Banco
Migration: `0006_crm_stabilization`

## Upgrade
```bash
alembic upgrade head
pytest -q
```
