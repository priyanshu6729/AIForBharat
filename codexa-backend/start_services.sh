#!/bin/bash
set -e

source .venv/bin/activate

echo "🚀 Starting Codexa Backend Services..."
echo ""

# Start Main API
echo "📡 Main API (port 8000)..."
uvicorn app.main:app --reload --port 8000 &
sleep 3

# Start Ingestion Service
echo "📥 Ingestion Service (port 8001)..."
PYTHONPATH=. uvicorn services.ingestion.app.main:app --reload --port 8001 &
sleep 3

# Start Analysis Service
echo "🔍 Analysis Service (port 8002)..."
PYTHONPATH=. uvicorn services.analysis.app.main:app --reload --port 8002 &
sleep 3

# Start Query Service
echo "💬 Query Service (port 8003)..."
PYTHONPATH=. uvicorn services.query.app.main:app --reload --port 8003 &
sleep 3

echo ""
echo "================================================================"
echo "🎉 ALL SERVICES STARTED SUCCESSFULLY!"
echo "================================================================"
echo ""
echo "📖 API Documentation:"
echo "   Main API:      http://127.0.0.1:8000/docs"
echo "   Ingestion:     http://127.0.0.1:8001/docs"
echo "   Analysis:      http://127.0.0.1:8002/docs"
echo "   Query:         http://127.0.0.1:8003/docs"
echo ""
echo "�� AI Model:      Amazon Nova Micro (2024)"
echo "�� AWS Credits:   $100 available"
echo "⚡ Cost:          ~$0.035 per 1M tokens"
echo ""
echo "Press Ctrl+C to stop all services"
echo ""

wait
