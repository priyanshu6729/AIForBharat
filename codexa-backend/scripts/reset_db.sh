#!/bin/bash

set -e

echo "⚠️  WARNING: This will delete all data!"
read -p "Are you sure? (yes/no): " confirm

if [ "$confirm" != "yes" ]; then
    echo "❌ Aborted"
    exit 1
fi

echo "🗑️  Dropping database..."
dropdb codexa || true

echo "🆕 Creating database..."
createdb codexa

echo "🔄 Running migrations..."
alembic upgrade head

echo "🌱 Seeding database..."
python scripts/seed_db.py

echo "✅ Database reset complete!"