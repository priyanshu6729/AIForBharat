# AIForBharat - Codexa

Codexa is an AI-powered code mentor platform that helps developers understand code step-by-step using analysis, guided explanations, and interactive workspace tooling.

This repository is a monorepo containing both backend and frontend applications.

## Repository Layout

- `codexa-backend/` - FastAPI backend (auth, analysis, guidance/chat, learning/progress, session APIs)
- `codexa-frontend/` - Next.js 14 frontend (mentor intake + workspace UI)
- `postgres-pgvector/` - local database helper assets
- `test_all_endpoints.sh` - quick API smoke script against deployed backend

## Architecture

- Frontend: Next.js App Router + TypeScript + Tailwind
- Backend: FastAPI + SQLAlchemy + Alembic + PostgreSQL
- Auth: AWS Cognito JWT-based auth
- AI: AWS Bedrock primary models with local fallback logic
- Deploy: Railway (backend currently configured via root `railway.toml`)

## Prerequisites

- Python 3.11+
- Node.js 18+
- npm 9+
- PostgreSQL (local) or managed Postgres (Railway/Supabase)
- AWS credentials and Cognito/Bedrock setup (for full feature set)

## Local Development

### 1) Backend

```bash
cd codexa-backend
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Set required values in `.env` (at minimum):

- `DATABASE_URL`
- `S3_BUCKET`
- `SECRET_KEY`
- `COGNITO_USER_POOL_ID`
- `COGNITO_CLIENT_ID`
- `COGNITO_REGION`

Run migrations and start backend:

```bash
alembic upgrade head
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

Backend health: `http://localhost:8000/health`

### 2) Frontend

```bash
cd codexa-frontend
npm install
```

Create `codexa-frontend/.env.local` with:

```env
NEXT_PUBLIC_BACKEND_URL=http://localhost:8000
COGNITO_CLIENT_ID=<your-cognito-client-id>
COGNITO_TOKEN_ENDPOINT=<your-cognito-token-endpoint>
COOKIE_DOMAIN=
COGNITO_USER_POOL_ID=<your-user-pool-id>
COGNITO_REGION=<your-region>
```

Run frontend:

```bash
npm run dev
```

Frontend: `http://localhost:3000`

## Useful Commands

### Backend tests

```bash
cd codexa-backend
source .venv/bin/activate
pytest -q tests/unit
```

### Backend live smoke test

```bash
cd codexa-backend
TOKEN=<jwt_token> BASE_URL=http://127.0.0.1:8000 python scripts/smoke_test_live.py
```

### Root-level deployed endpoint check

```bash
./test_all_endpoints.sh
```

## Deployment (Railway)

Root `railway.toml` is set to build backend from `codexa-backend/Dockerfile`.

Important backend deploy env vars:

- `DATABASE_URL`
- `S3_BUCKET`
- `ENV=production`
- `RUN_MIGRATIONS=true`
- `ALLOW_START_WITHOUT_MIGRATIONS=false`

Startup behavior (from `codexa-backend/start.sh`):

- Runs `alembic upgrade head` by default before app boot
- Refuses to start if migrations fail (unless explicitly overridden)

## Troubleshooting

### `relation "users" does not exist` / `relation "learning_paths" does not exist`

Migrations have not been applied.

```bash
cd codexa-backend
alembic upgrade head
```

### Alembic interpolation errors (`%(DATABASE_URL)s` / `%40`)

Latest backend code avoids interpolation-sensitive migration setup. Ensure you deploy the latest backend changes.

### `password authentication failed for user "postgres"`

Your `DATABASE_URL` credentials are incorrect.

- Copy the connection string directly from your DB provider dashboard.
- If using Supabase pooler (`:6543`), verify required username format (often `postgres.<project_ref>`).
- Use normal URL encoding once (`@` -> `%40`), not `%%40`.
- After repeated failures, wait briefly for provider circuit breaker to clear.

## API Surface (Backend)

Major endpoints include:

- Auth: `/api/auth/register`, `/api/auth/login`, `/api/auth/me`
- Mentor: `/api/guidance`, `/api/chat`, `/api/chat/stream`
- Code: `/api/analyze`, `/api/execute`, `/api/visualize`
- Learning: `/api/learn/paths`, `/api/progress`
- Health: `/health`, `/health/detailed`

## Notes

- Backend is the source of truth for mentor model routing and fallback.
- Frontend calls backend through internal BFF handlers in frontend app architecture.
- Keep backend and frontend env configuration aligned when switching between local and production.
