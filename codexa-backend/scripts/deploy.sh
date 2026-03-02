#!/bin/bash

set -e

echo "🚀 Starting deployment..."

# Check if environment is set
if [ -z "$1" ]; then
    echo "Usage: ./scripts/deploy.sh [staging|production]"
    exit 1
fi

ENVIRONMENT=$1

echo "📦 Deploying to $ENVIRONMENT..."

# Run tests
echo "🧪 Running tests..."
pytest

# Build Docker image
echo "🐳 Building Docker image..."
docker build -t codexa-backend:$ENVIRONMENT .

# Tag for deployment
if [ "$ENVIRONMENT" == "production" ]; then
    echo "🏷️  Tagging for production..."
    docker tag codexa-backend:production your-registry/codexa-backend:latest
    docker push your-registry/codexa-backend:latest
fi

echo "✅ Deployment complete!"