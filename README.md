# CS Platform — Sprint 1 Backend

Implementação inicial executável do CS Recupera Enterprise.

## Entregue
- FastAPI e Swagger;
- autenticação OAuth2/JWT;
- hashing Argon2;
- organização inicial e administrador automático;
- usuários e papéis básicos;
- CRUD de clientes com isolamento por organização;
- auditoria de criação/alteração;
- SQLite para testes locais;
- PostgreSQL via Docker;
- Alembic;
- testes automatizados.

## Execução simples (sem Docker)
```bash
cd backend
python -m venv .venv
.venv\\Scripts\\activate
pip install -r requirements.txt
copy .env.example .env
uvicorn app.main:app --reload
```
Abra http://localhost:8000/docs

## Login inicial
- usuário: `admin@csrecupera.com.br`
- senha: `ChangeMe123!`

Altere imediatamente em ambiente real.

## Testes
```bash
cd backend
pytest -q
```

## PostgreSQL com Docker
```bash
docker compose up --build
```

## Rotas principais
- POST `/api/v1/auth/token`
- GET `/api/v1/auth/me`
- POST/GET `/api/v1/users`
- POST/GET/PATCH `/api/v1/clients`
- GET `/api/v1/health`
