# infrastructure/docker

Home for shared Docker assets that do not belong to a single service (for example a future
reverse proxy or database init scripts). Service-specific files stay with their service:

- `backend/Dockerfile` — multi-stage (`development`, `production`)
- `frontend/Dockerfile` + `frontend/nginx.conf` — multi-stage (`development`, `build`, `production`)
- `docker-compose.yml` (repository root) — development environment
