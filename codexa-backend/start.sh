#!/bin/bash
# Start script that handles PORT variable properly

set -e

# Get port from environment or default to 8000
PORT=${PORT:-8000}

echo "Starting uvicorn on port $PORT..."

# Run migrations if needed
if [ "$RUN_MIGRATIONS" = "true" ]; then
    echo "Running database migrations..."
    alembic upgrade head
fi

# Start the application
exec uvicorn app.main:app --host 0.0.0.0 --port "$PORT"
