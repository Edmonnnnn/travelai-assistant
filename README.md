# TravelAI Assistant (HITL) — Monorepo

## Quick start (dev)
1) Copy `.env.example` → `.env`
2) Run: `make up` (or project wrapper)
3) Open:
- Frontend: http://localhost:${FRONTEND_PORT}
- Backend health: http://localhost:${BACKEND_PORT}/health

> MVP note: no auto-send / auto-confirm. DRAFT only.

## Repository layout
- backend/  — FastAPI (API, migrations, health, config)
- frontend/ — Next.js (UI, proxy/config)
- infra/    — docker-compose, nginx (optional), monitoring stubs (optional)
- ops/      — dev scripts, migrations/seed helpers
- docs/     — diagrams, checklists, product docs

## Ports
| Service   | Default |
|----------|---------|
| Frontend | 3000    |
| Backend  | 8000    |
| Postgres | 5432    |

## Degraded mode (required)
- If `OPENAI_API_KEY` is empty: API must not crash; AI endpoints return a clear message that AI is disabled.
- If vector store is unavailable: API must not crash; vector/search features return a clear message and log one warning (no spam).

## Troubleshooting
- Ports already in use
- Docker Desktop / WSL2 (Windows)
- Backend can’t reach DB
- Frontend can’t reach backend (BASE_URL/CORS)
