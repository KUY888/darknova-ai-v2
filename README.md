# DARKNOVA AI V2

AI Assistant (FastAPI) by **KUY888 (คุณลีโอ)** — chat, coding, debugging and planning. Built to grow into Web/Android/PWA/Public API.

> **Status:** code written and statically checked only. `pytest` and server startup have **not been run** yet (see Testing).

## Features
Multiple conversations, history, search/rename/delete, AI modes (CHAT/CODE/DEBUG/PLAN), JWT auth with logout (token revocation), user + public profile with avatar, App Profile page, system status, rate limiting, CORS.

## Requirements & Installation
Python 3.11+.
```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env     # then edit .env
python run.py            # http://127.0.0.1:8000  (docs: /docs, App Profile: /app-profile)
```

## Environment Variables
| Name | Purpose |
|---|---|
| `AI_PROVIDER` | `groq`, `openai` or `openrouter` |
| `AI_MODEL` | empty = provider default |
| `AI_API_KEY` | provider key (server-side only) |
| `AI_BASE_URL` | optional override for any OpenAI-compatible API |
| `DATABASE_URL` | default `sqlite:///./darknova.db` |
| `SECRET_KEY` | **required**, 16+ chars: `python -c "import secrets;print(secrets.token_urlsafe(48))"` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | default 60 |
| `CORS_ORIGINS` | comma-separated origins |
| `RATE_LIMIT_ENABLED`, `UPLOAD_DIR`, `GITHUB_URL` | optional |

## Database
SQLAlchemy 2. Tables: `users`, `conversations`, `messages`, `revoked_tokens`. Tables are auto-created on startup (add Alembic before production schema changes). PostgreSQL: set `DATABASE_URL=postgresql+psycopg://...` and install `psycopg`.

## AI Provider
`app/providers/` — add a provider by subclassing `AIProvider` and registering it in `providers/__init__.py`. The chat service never depends on a concrete provider. `/system/status` reports **configured** (key present), not a live ping.

## Authentication
`POST /auth/register`, `/auth/login` (username or email), `/auth/logout` (revokes the token's `jti`). Passwords hashed with bcrypt (max 72 bytes). Email verification / password reset columns exist but are not implemented.

## Profile / App Profile
`GET|PATCH /users/me`, `POST|DELETE /users/me/avatar` (PNG/JPEG/WEBP, ≤2MB, magic-byte check), `GET /users/{username}` (public: no email/secrets). App Profile UI: `/app-profile`, data from `/system/about` and `/system/status`; logo: `app/static/logo.jpg`.

## API
All responses: `{"success": true, "data": ...}` or `{"success": false, "error": "..."}`.
`/health`, `/auth/*`, `/users/*`, `/conversations` (+`?q=` search, `/{id}`, `/{id}/messages`), `/chat`, `/system/status`, `/system/about`. Interactive docs at `/docs`.

## Testing
```bash
pytest -q
```
Tests use a temp SQLite DB and a fake AI provider (no network).

## Troubleshooting
- `SECRET_KEY must be set` → fill it in `.env`.
- 503 on chat → `AI_API_KEY` missing/invalid provider name.
- 502 on chat → upstream provider error (check key/model).

## Security
No hard-coded secrets, `.env` git-ignored, bcrypt hashes never returned, ownership checks return 404, in-memory rate limiting (use Redis behind multiple workers), CORS allow-list, generic 500 errors.

## Developer / Discord
KUY888 (คุณลีโอ) — DARKNOVA COMMUNITY: https://discord.gg/E4gp2jSg3F
