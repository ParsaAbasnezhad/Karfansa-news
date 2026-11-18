# infrastructure/docker

Shared deployment assets live here. See `docs/deployment.md` for the release,
backup, restore, and rollback procedure. Service-specific files stay with
their service:

- `backend/Dockerfile` — multi-stage (`development`, `production`)
- `frontend/Dockerfile` + `frontend/nginx.conf` + `frontend/nginx-main.conf` —
  multi-stage build and non-root production Nginx
- `nginx-host.example.conf` — example TLS ingress on the Docker host
- `docker-compose.yml` (repository root) — development environment
- `docker-compose.production.yml` (repository root) — production services
