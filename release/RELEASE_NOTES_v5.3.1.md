# CS Platform v5.3.1 — Security & Observability

Release de estabilização da v5.3.0.

## Entregas
- Rate limiting por IP, com política reforçada nos endpoints de login.
- Cabeçalhos HSTS, CSP, COOP e CORP.
- Métricas OpenMetrics em `/metrics`.
- Contadores de requisições e soma de latência por método, rota e status.
- Request ID, correlation ID e tempo de resposta preservados.
- Configuração integral por variáveis de ambiente.

## Compatibilidade
Sem nova migration. Compatível diretamente com o banco da v5.3.0.
