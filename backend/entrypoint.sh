#!/bin/sh
set -e

# CLI passthrough: "docker compose run backend alembic ..."
if [ "${1:-}" = "alembic" ]; then
  shift
  exec alembic "$@"
fi

echo "▶ DATABASE_URL=${DATABASE_URL:-<empty>}"

echo "▶ Running migrations..."
if [ -f /app/alembic.ini ]; then
  alembic upgrade head
  echo "▶ Migrations applied: $(alembic current || true)"
else
  echo "⚠ Alembic not configured (alembic.ini not found). Skipping migrations."
fi

if [ "${SEED_DATA:-false}" = "true" ]; then
  echo "▶ Running seed..."
  python - <<'PY'
from sqlalchemy.exc import ProgrammingError, IntegrityError
from app.db import SessionLocal

try:
    from app.seed import run_seed
except Exception:
    print("▶ Seed module not found. Skipping seed.")
    raise SystemExit(0)

db = SessionLocal()
try:
    try:
        applied = run_seed(db)
        print("▶ Seed applied" if applied else "▶ Seed skipped (already present)")
    except ProgrammingError:
        db.rollback()
        print("▶ Seed skipped (schema not ready)")
    except IntegrityError:
        db.rollback()
        print("▶ Seed skipped (integrity/unique constraint)")
except Exception as e:
    # Важно: seed не должен валить контейнер в ноль
    print(f"⚠ Seed failed (non-fatal): {e}")
finally:
    db.close()
PY
else
  echo "▶ Seed skipped"
fi

echo "▶ Starting FastAPI"

# If container command is uvicorn, disable default access logs to reduce noise.
# We keep only our structured JSON logs from AccessLogMiddleware.
if [ "${1:-}" = "uvicorn" ]; then
  has_access_log_flag=false

  for arg in "$@"; do
    if [ "$arg" = "--access-log" ] || [ "$arg" = "--no-access-log" ]; then
      has_access_log_flag=true
      break
    fi
  done

  if [ "$has_access_log_flag" = "false" ]; then
    exec "$@" --no-access-log
  fi
fi

exec "$@"
