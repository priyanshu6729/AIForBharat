#!/usr/bin/env bash
set -euo pipefail

REPO_URL=${REPO_URL:-}
APP_DIR=${APP_DIR:-/opt/codexa}
BRANCH=${BRANCH:-main}
PYTHON_BIN=${PYTHON_BIN:-python3}

if [ -z "$REPO_URL" ]; then
  echo "REPO_URL is required. Example: REPO_URL=git@github.com:you/codexa.git"
  exit 1
fi

sudo apt-get update
sudo apt-get install -y git "$PYTHON_BIN" "$PYTHON_BIN-venv" "$PYTHON_BIN"-pip build-essential

sudo mkdir -p "$APP_DIR"
sudo chown "$USER":"$USER" "$APP_DIR"

if [ ! -d "$APP_DIR/.git" ]; then
  git clone --branch "$BRANCH" "$REPO_URL" "$APP_DIR"
else
  cd "$APP_DIR"
  git fetch origin
  git checkout "$BRANCH"
  git pull --ff-only origin "$BRANCH"
fi

if [ -d "$APP_DIR/codexa-backend" ]; then
  BACKEND_DIR="$APP_DIR/codexa-backend"
else
  BACKEND_DIR="$APP_DIR"
fi

cd "$BACKEND_DIR"

$PYTHON_BIN -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

if [ ! -f ".env" ] && [ -f ".env.example" ]; then
  cp .env.example .env
  echo "Created .env from .env.example. Please edit .env with production values."
fi

if [ -f "alembic.ini" ]; then
  .venv/bin/alembic upgrade head || true
fi

cat <<SERVICE | sudo tee /etc/systemd/system/codexa.service
[Unit]
Description=Codexa Backend
After=network.target

[Service]
User=$USER
WorkingDirectory=$BACKEND_DIR
EnvironmentFile=$BACKEND_DIR/.env
ExecStart=$BACKEND_DIR/.venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 1
Restart=always

[Install]
WantedBy=multi-user.target
SERVICE

sudo systemctl daemon-reload
sudo systemctl enable codexa
sudo systemctl restart codexa

echo "Codexa backend deployed and running on port 8000"
