#!/bin/bash

set -e

echo "🔧 Setting up Codexa Backend..."

# Check Python version
echo "📋 Checking Python version..."
python3 --version

# Create virtual environment
echo "🐍 Creating virtual environment..."
python3 -m venv .venv

# Activate virtual environment
echo "✅ Activating virtual environment..."
source .venv/bin/activate

# Install dependencies
echo "📦 Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Copy environment file
if [ ! -f .env ]; then
    echo "📝 Creating .env file..."
    cp .env.example .env
    echo "⚠️  Please update .env with your configuration"
fi

# Setup database
echo "🗄️  Setting up database..."
createdb codexa || echo "Database might already exist"

# Run migrations
echo "🔄 Running migrations..."
alembic upgrade head

echo "✅ Setup complete!"
echo "👉 Run: source .venv/bin/activate && uvicorn app.main:app --reload"