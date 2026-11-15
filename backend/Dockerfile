# syntax=docker/dockerfile:1
FROM python:3.12-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_LINK_MODE=copy \
    UV_COMPILE_BYTECODE=1 \
    UV_PROJECT_ENVIRONMENT=/opt/venv \
    PATH="/opt/venv/bin:$PATH"

COPY --from=ghcr.io/astral-sh/uv:0.11 /uv /usr/local/bin/uv

RUN groupadd --system --gid 1000 app \
    && useradd --system --uid 1000 --gid app --create-home app \
    && mkdir -p /app /opt/venv \
    && chown app:app /app /opt/venv

WORKDIR /app
USER app

# Dependencies are installed before the source is copied to maximise layer caching.
COPY --chown=app:app pyproject.toml uv.lock ./


# ---------------------------------------------------------------- development
FROM base AS development
RUN uv sync --frozen --no-install-project
COPY --chown=app:app . .
EXPOSE 8000
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]


# ----------------------------------------------------------------- production
FROM base AS production
ENV DJANGO_SETTINGS_MODULE=config.settings.production
RUN uv sync --frozen --no-install-project --no-dev
COPY --chown=app:app . .
EXPOSE 8000
CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "3"]
