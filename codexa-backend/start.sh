#!/bin/bash
set -e

# Railway sets PORT environment variable
export PORT=${PORT:-8000}

echo "========================================="
echo "Starting Codexa Backend"
echo "========================================="
echo "PORT: $PORT"
echo "ENV: ${ENV:-not set}"
echo "DATABASE_URL: ${DATABASE_URL:+set}"
echo "S3_BUCKET: ${S3_BUCKET:-not set}"
echo "RAILWAY_ENVIRONMENT: ${RAILWAY_ENVIRONMENT:-not set}"
echo "========================================="

# Check required environment variables
if [ -z "$DATABASE_URL" ]; then
    echo "ERROR: DATABASE_URL is not set!"
    echo "Please add a PostgreSQL database in Railway"
    exit 1
fi

if [ -z "$S3_BUCKET" ]; then
    echo "ERROR: S3_BUCKET is not set!"
    echo "Please set environment variables in Railway dashboard"
    exit 1
fi

# Run migrations by default to keep production schema in sync.
# Set RUN_MIGRATIONS=false only for special cases.
RUN_MIGRATIONS_VALUE=$(echo "${RUN_MIGRATIONS:-true}" | tr '[:upper:]' '[:lower:]')
ALLOW_START_WITHOUT_MIGRATIONS_VALUE=$(echo "${ALLOW_START_WITHOUT_MIGRATIONS:-false}" | tr '[:upper:]' '[:lower:]')

if [ "$RUN_MIGRATIONS_VALUE" = "true" ]; then
    echo "Running database migrations (alembic upgrade head)..."
    if ! alembic upgrade head; then
        if [ "$ALLOW_START_WITHOUT_MIGRATIONS_VALUE" = "true" ]; then
            echo "⚠ Migrations failed, but ALLOW_START_WITHOUT_MIGRATIONS=true so continuing startup."
        else
            echo "❌ Migrations failed. Refusing to start to avoid runtime 500s."
            exit 1
        fi
    fi
else
    echo "RUN_MIGRATIONS=false, skipping migrations."
fi

echo "Starting uvicorn on 0.0.0.0:$PORT..."

# Convert LOG_LEVEL to lowercase for uvicorn
LOG_LEVEL_LOWER=$(echo "${LOG_LEVEL:-info}" | tr '[:upper:]' '[:lower:]')

# Start the application - ensure it binds to 0.0.0.0
exec uvicorn app.main:app \
    --host 0.0.0.0 \
    --port $PORT \
    --log-level "$LOG_LEVEL_LOWER" \
    --access-log
