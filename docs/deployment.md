# Production deployment and recovery

This repository supports a single-host Docker Compose deployment behind a
**host-managed HTTPS reverse proxy**. No hosting provider, public hostname,
certificate issuer, or mail/SMS provider is assumed. `docker-compose.yml` is
for local development; production uses `docker-compose.production.yml` and
separate `karfansa-news-production_*` volumes. Database and Redis have no
published ports. The frontend listens only on host loopback port 8080 by
default; Gunicorn, PostgreSQL, and Redis are reachable only on Compose networks.

The commands below are for a POSIX shell on the deployment host, from the
repository root. Keep the host patched, restrict access to `.env.production`,
and provide durable storage for the Docker volumes. Run commands with Docker
Compose v2. Never run `docker compose down -v` on a data-bearing deployment.

## One-time prerequisites

1. Set a public hostname and valid TLS certificate on a trusted host proxy.
   Adapt `infrastructure/docker/nginx-host.example.conf` to that host. It must
   overwrite `Host`, `X-Forwarded-Proto`, `X-Forwarded-For`, and `X-Real-IP`.
   If behind a CDN or another proxy, configure and verify its trusted client
   IP ranges at the host proxy before enabling per-IP auth rate limits.
2. Copy `.env.production.example` to `.env.production`, replace all
   `REPLACE_` placeholders, and set permissions to `0600`. Use a strong random
   Django key (at least 50 characters) and URL-safe random database and Redis
   passwords. Production Redis requires authentication; the cache, Celery
   broker, and result backend use the same password. Set the exact hostname in
   `DJANGO_ALLOWED_HOSTS` and its HTTPS origin in
   `DJANGO_CSRF_TRUSTED_ORIGINS`. Configure working SMTP and a working SMS
   provider: the current frontend exposes both account flows. Store secrets in
   the host secret manager where available. Never copy them into a frontend
   `VITE_` variable.
3. Verify the host proxy is the only way into the loopback frontend port.
   `DJANGO_TRUST_X_FORWARDED_PROTO=true` and `DJANGO_TRUST_X_REAL_IP=true`
   are safe only for this topology. Set both to `false` if that trust boundary
   is absent; then adapt HTTPS handling before exposing traffic.
4. Keep HSTS at zero until HTTPS and redirects are verified. Only then set a
   positive `DJANGO_SECURE_HSTS_SECONDS` (eventually 31536000). Enable
   subdomain coverage or preload only after checking every affected
   subdomain and satisfying preload requirements. The application does not
   assume those conditions.

```sh
cp .env.production.example .env.production
chmod 600 .env.production
# Edit .env.production and install the TLS host proxy before continuing.
docker compose --env-file .env.production -f docker-compose.production.yml config -q
docker compose --env-file .env.production -f docker-compose.production.yml build
docker compose --env-file .env.production -f docker-compose.production.yml run --rm --no-deps frontend nginx -t
docker compose --env-file .env.production -f docker-compose.production.yml up -d db redis
```

## Preflight and release

Run these against the intended production images. The first deployment has
no existing data to back up; every later deployment requires a verified
database and media backup before migrations. Review `migrate --plan` for
destructive operations before running `migrate`. The example production HSTS
value of zero can produce a deployment-check warning until HTTPS is verified.
Treat all other warnings as blockers unless documented and accepted.

```sh
docker compose --env-file .env.production -f docker-compose.production.yml run --rm backend python manage.py check
docker compose --env-file .env.production -f docker-compose.production.yml run --rm backend python manage.py check --deploy
docker compose --env-file .env.production -f docker-compose.production.yml run --rm backend python manage.py makemigrations --check --dry-run
docker compose --env-file .env.production -f docker-compose.production.yml run --rm backend python manage.py migrate --plan
# Take and verify the backups below before this command on an existing site.
docker compose --env-file .env.production -f docker-compose.production.yml run --rm backend python manage.py migrate --noinput
docker compose --env-file .env.production -f docker-compose.production.yml run --rm backend python manage.py collectstatic --noinput
docker compose --env-file .env.production -f docker-compose.production.yml up -d backend celery_worker celery_beat frontend
docker compose --env-file .env.production -f docker-compose.production.yml ps
docker compose --env-file .env.production -f docker-compose.production.yml logs --tail=100 backend celery_worker celery_beat frontend
```

Keep exactly one `celery_beat` replica. Review the ingestion lock and queue
health before changing worker concurrency or the 15-minute RSS schedule.

Verify the public HTTPS origin using its real hostname. Check that the session
and CSRF cookies have `Secure`, login and logout work, a new article appears,
media and admin static files load, and `/api/v1/health/` reports healthy.
`SESSION_COOKIE_HTTPONLY` is enabled. `CSRF_COOKIE_HTTPONLY` remains disabled
because the same-origin React client reads the CSRF cookie and sends
`X-CSRFToken` on writes; changing it alone would break account and contact
forms. CSRF origin checking and Secure/SameSite cookies remain enabled.
`/unknown-route` must return 404 with the Persian page; Django backend errors
must return an opaque 500 page. The host proxy must not expose its own trace or
internal address. The API must return JSON errors even if the backend is down.
The frontend CSP is report-only; inspect browser violations on staging before
any enforced policy, especially the article structured-data script.

```sh
PUBLIC_HOST=REPLACE_WITH_PUBLIC_HOSTNAME
curl --fail --show-error --head "https://$PUBLIC_HOST/"
curl --fail --show-error "https://$PUBLIC_HOST/api/v1/health/"
curl --show-error --head "https://$PUBLIC_HOST/unknown-route"
curl --show-error --head "https://$PUBLIC_HOST/sitemap.xml"
```

The production React build always uses the relative `/api/v1` URL. The
Nginx route allowlist in `frontend/nginx.conf` must be updated when React
routes change, so unknown paths retain genuine HTTP 404 status. The frontend
provides standalone 404/500 HTML as well as client-side error screens.
For a missing dynamic news ID or editorial slug, static SPA hosting cannot
know record existence before JavaScript loads; those direct URLs still get an
HTTP 200 shell, even if React displays a 404. Server rendering or an ingress
lookup is needed to close that SEO/status gap.

## Backup

Use an encrypted, access-controlled off-host backup destination and test
restoration regularly. PostgreSQL dumps do not contain uploaded media. The
following creates separate database and media archives without stopping the
site; for a fully consistent snapshot during active publishing, briefly pause
writers and workers or use a storage snapshot coordinated with the database.

```sh
mkdir -p backups
chmod 700 backups
BACKUP_STAMP=$(date -u +%Y%m%dT%H%M%SZ)
git rev-parse HEAD > "backups/karfansa-news-$BACKUP_STAMP.revision"
docker compose --env-file .env.production -f docker-compose.production.yml exec -T db sh -c 'exec pg_dump -U "$POSTGRES_USER" -d "$POSTGRES_DB" -Fc' > "backups/karfansa-news-$BACKUP_STAMP.dump"
docker compose --env-file .env.production -f docker-compose.production.yml exec -T backend tar -C /app/media -czf - . > "backups/karfansa-news-media-$BACKUP_STAMP.tar.gz"
test -s "backups/karfansa-news-$BACKUP_STAMP.dump"
test -s "backups/karfansa-news-media-$BACKUP_STAMP.tar.gz"
docker compose --env-file .env.production -f docker-compose.production.yml exec -T db pg_restore --list < "backups/karfansa-news-$BACKUP_STAMP.dump" > /dev/null
tar -tzf "backups/karfansa-news-media-$BACKUP_STAMP.tar.gz" > /dev/null
```

Keep a dated backup and the matching Git revision. A successful archive/list
check is necessary but does not replace a test restore.

## Restore and rollback

First rehearse on an isolated staging deployment with its own volumes. A
production restore overwrites current database content and media, so take a
fresh snapshot and schedule a maintenance window before these operator actions.
Do not run them as part of automated startup. Stop every writer, then restore
the matching database dump and media archive:

```sh
BACKUP_STAMP=REPLACE_WITH_VERIFIED_ARCHIVE_STAMP
docker compose --env-file .env.production -f docker-compose.production.yml stop frontend backend celery_worker celery_beat
docker compose --env-file .env.production -f docker-compose.production.yml exec -T db sh -c 'exec pg_restore -U "$POSTGRES_USER" -d "$POSTGRES_DB" --clean --if-exists --single-transaction --exit-on-error' < "backups/karfansa-news-$BACKUP_STAMP.dump"
docker compose --env-file .env.production -f docker-compose.production.yml run --rm --no-deps -T --entrypoint tar backend -C /app/media -xzf - < "backups/karfansa-news-media-$BACKUP_STAMP.tar.gz"
docker compose --env-file .env.production -f docker-compose.production.yml up -d backend celery_worker celery_beat frontend
```

For a code-only rollback, return to the recorded prior Git revision, rebuild,
and restart only if its schema remains compatible. Do not reverse migrations
blindly. If a release changed schema incompatibly, restore the matching
database/media backup under the maintenance procedure above. Recheck health,
authentication, editorial publishing, 404/500 behavior, and worker logs before
reopening traffic.

## Remaining infrastructure decisions

- Choose hostname, TLS proxy/certificate, monitoring, log retention, and
  off-host backup location.
- Verify SMTP/SMS delivery and all authentication flows on staging.
- Verify host-level firewalls, proxy header sanitation, time sync, and outbound
  RSS access. Docker alone does not provide these controls.
- Set resource limits and worker concurrency based on measured production load;
  the Compose file constrains process counts but does not assume machine size.
