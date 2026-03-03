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

# Run migrations if needed
if [ "$RUN_MIGRATIONS" = "true" ]; then
    echo "Running database migrations..."
    alembic upgrade head
fi

echo "Starting uvicorn on port $PORT..."

# Start the application with more verbose logging
exec uvicorn app.main:app \
    --host 0.0.0.0 \
    --port $PORT \
    --log-level ${LOG_LEVEL:-info} \
    --access-log \
    --use-colors
