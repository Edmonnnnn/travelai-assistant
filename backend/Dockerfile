FROM python:3.10-slim

WORKDIR /app

# (опционально) системные зависимости для uvicorn[standard]
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential procps iproute2 \
 && rm -rf /var/lib/apt/lists/*


# Python deps
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# App code
COPY app ./app

EXPOSE 8810

# Alembic (migrations)
COPY alembic.ini /app/alembic.ini
COPY alembic /app/alembic


# Use env var BACKEND_PORT if provided, else 8810
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${BACKEND_PORT:-8810}"]

COPY entrypoint.sh /app/entrypoint.sh
ENTRYPOINT ["sh", "-c", "sh /app/entrypoint.sh"]
