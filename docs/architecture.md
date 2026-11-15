# Architecture notes

## Modular monolith
One Django project; each capability becomes an app under `backend/apps/`. Apps communicate through
Python imports of each other's public modules, never through HTTP. Extract a service only when a
real scaling need appears.

## Backend layering (convention for future apps)
`models.py` (data) → `services.py` (business logic) → `api.py` (Django Ninja router, thin).
Routers are mounted in `apps/core/api.py` under `/api/v1/`.

## Settings
`config/settings/base.py` holds shared configuration read from environment variables.
`development.py` / `production.py` re-export base explicitly (no wildcard imports) and override only
what differs. Select with `DJANGO_SETTINGS_MODULE`.

## Errors and logging
- Raise subclasses of `apps.common.exceptions.AppError` for expected failures; they are rendered as
  `{"error": {"code", "message", "details?"}}`. Validation → 422, unexpected → 500 (logged).
- Logs are JSON lines on stdout (`apps.common.logging.JsonFormatter`); extra fields passed via
  `logger.info(..., extra={...})` are included.

## Frontend
`app/` wiring (providers, router, query client, error boundary) · `features/<name>/` per feature ·
`components/ui` reusable primitives · `components/layout` shells · `lib/api-client.ts` the only place
that calls `fetch` · `services/` typed API calls · `hooks/` shared query hooks · `styles/` design
tokens + reset + global CSS (components use CSS Modules).
