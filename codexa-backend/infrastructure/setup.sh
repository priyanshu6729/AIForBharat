#!/usr/bin/env bash
set -euo pipefail

sudo apt-get update
sudo apt-get install -y python3.11 python3.11-venv python3-pip nodejs npm

python3.11 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

mkdir -p models
if [ ! -f "models/tinyllama.gguf" ]; then
  echo "Download TinyLlama GGUF into models/tinyllama.gguf"
fi

cat <<SERVICE | sudo tee /etc/systemd/system/codexa.service
[Unit]
Description=Codexa Backend
After=network.target

[Service]
User=ubuntu
WorkingDirectory=$(pwd)
EnvironmentFile=$(pwd)/.env
ExecStart=$(pwd)/.venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 1
Restart=always

[Install]
WantedBy=multi-user.target
SERVICE

sudo systemctl daemon-reload
sudo systemctl enable codexa
sudo systemctl restart codexa
