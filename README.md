# TravelAI Assistant (HITL)

Monorepo with a FastAPI backend and Next.js frontend, run locally via Docker Compose.
Principle: Human-in-the-loop only (no auto-send, no auto-confirm).

## Quick start (3 steps)

1) Copy env template:

```bash
# macOS / Linux
cp .env.example .env

# Windows (PowerShell)
copy .env.example .env
```

2) Start the stack (from repo root):

```bash
# macOS / Linux
make up

# Windows (PowerShell)
.\dev.ps1 up
```

3) Verify endpoints:

- Frontend: http://localhost:3000
- Backend health: http://localhost:8810/health
- Frontend health proxy: http://localhost:3000/api/health
- Users API proxy: http://localhost:3000/api/users
  - Health response includes `ai_enabled` and `vector_enabled` flags for degraded-mode signaling.

## Ports

| Service   | Default Port | Env var       | Notes |
|-----------|--------------|---------------|-------|
| Frontend  | 3000         | FRONTEND_PORT | Next.js app |
| Backend   | 8810         | BACKEND_PORT  | FastAPI service |
| Postgres  | 5432         | DB_PORT       | Postgres container |

## Troubleshooting

- Ports busy: edit `FRONTEND_PORT`, `BACKEND_PORT`, or `DB_PORT` in `.env`, then re-run `make up` or `.\dev.ps1 up`.
- Postgres password trap: changing `POSTGRES_PASSWORD` after the `pgdata` volume exists will fail auth. Use `docker compose -f infra/docker-compose.yml down -v` to reset (data loss).
- Frontend cannot reach backend: confirm `http://localhost:8810/health` is OK and `BACKEND_INTERNAL_URL` is `http://backend:8810` in `.env` for compose.
- Migrations/seed: backend runs `alembic upgrade head` at startup; set `SEED_DATA=true` in `.env` to load demo users on start.

## FAQ

- No `OPENAI_API_KEY`: A1 backend does not use it yet; leaving it empty is fine.
- Optional external services: `QDRANT_URL` and `PGVECTOR_DSN` are passed through but not used by the current code; leave empty unless you wire them later.

## Stop

```bash
# macOS / Linux
make down

# Windows (PowerShell)
.\dev.ps1 down
```
