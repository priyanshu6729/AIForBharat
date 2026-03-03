#!/bin/bash
set -e

# Railway sets PORT environment variable
export PORT=${PORT:-8000}

echo "Starting uvicorn on port $PORT..."

# Run migrations if needed
if [ "$RUN_MIGRATIONS" = "true" ]; then
    echo "Running database migrations..."
    alembic upgrade head
fi

# Start the application - use exec to replace shell process
exec uvicorn app.main:app --host 0.0.0.0 --port $PORT
