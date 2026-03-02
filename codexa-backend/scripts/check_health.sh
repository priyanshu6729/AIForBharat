#!/bin/bash

# Check backend health
BASE_URL="${1:-http://localhost:8000}"

echo "🏥 Checking health of $BASE_URL..."

# Health check
HEALTH=$(curl -s "$BASE_URL/health")
echo "Health: $HEALTH"

if echo "$HEALTH" | grep -q "ok"; then
    echo "✅ Backend is healthy!"
    exit 0
else
    echo "❌ Backend is unhealthy!"
    exit 1
fi