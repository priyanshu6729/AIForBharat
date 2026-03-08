# Codexa Frontend v2

Production-ready Next.js 14 frontend for Codexa with:

- App Router + TypeScript + Tailwind
- BFF API routes for secure backend communication
- HttpOnly cookie auth with refresh-on-401 flow
- Mentor intake flow and interactive workspace
- Primary flow graph + secondary D3 animated graph
- Monaco editor, mentor chat streaming, output console, learning panel

## Setup

1. Copy `.env.example` to `.env.local`
2. Set values:
   - `NEXT_PUBLIC_BACKEND_URL`
   - `COGNITO_TOKEN_ENDPOINT`
   - `COGNITO_CLIENT_ID`
   - `COOKIE_DOMAIN` (optional)
3. Install dependencies:

```bash
npm install
```

4. Run dev server:

```bash
npm run dev
```

## Routes

- `/` landing
- `/auth/login`, `/auth/signup`, `/auth/verify`
- `/mentor`
- `/workspace`
- Compatibility aliases:
  - `/dashboard` -> `/workspace`
  - `/code-editor` -> `/workspace`
  - `/sessions` -> `/workspace?panel=sessions`

## API/BFF

Client calls only internal `/api/*` routes.

Protected routes forward bearer tokens from secure cookies and attempt Cognito refresh when backend returns 401.

Mutating calls require `x-codexa-intent: codexa-web`.
