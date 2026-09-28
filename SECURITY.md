# Address (PSGC) API - security and deployment notes

This service is **internal**: only the Django backend on the same server talks to it.

## Required
1. Put the shared secret in `.env` (the service refuses to start without it) and the SAME value in the Django backend's `.env`:
   ```
   INTERNAL_API_KEY=<64 random characters>
   ```
   Generate one: `python -c "import secrets; print(secrets.token_urlsafe(48))"`
2. Every request except `GET /ping` must send the header `X-Internal-Key: <that value>`.

## Run (production / staging)
Bind to localhost only and keep a single worker (the rate limiter is in-process). Run it under systemd:
```
uvicorn main:app --host 127.0.0.1 --port 8003 --no-server-header --workers 1
```
Never use `--reload` or `--host 0.0.0.0` on the server. Do not open port 8003 in the firewall.
Production and Staging each need their own instance, port and `.env` (different `INTERNAL_API_KEY`).

## Developer mode
`ENABLE_DOCS=true` turns on Swagger (`/docs`, use the *Authorize* button) and the landing page. Never enable it on the server.

## Limits (all optional, in `.env`)
_No send limits. `/barangays` paging is capped at `limit<=1000`._
## What is protected
- shared-secret header on all endpoints except `/ping` (constant-time comparison, fail-closed at startup)
- no CORS, no public docs, no static files, no `GET`-triggered actions
- input validation and rate limits (bounded paging)
- logs never contain full phone numbers / e-mail addresses / provider responses
