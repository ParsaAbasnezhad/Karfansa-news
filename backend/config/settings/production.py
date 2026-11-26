"""Production settings: base + hardened security defaults."""

from urllib.parse import urlsplit

from django.core.exceptions import ImproperlyConfigured

from config.settings import base

# Re-export base settings explicitly (no wildcard import).
globals().update({name: value for name, value in vars(base).items() if name.isupper()})

DEBUG = False
_seo_origin = urlsplit(SEO_SITE_URL)
if (
    _seo_origin.scheme != "https"
    or not _seo_origin.hostname
    or _seo_origin.username
    or _seo_origin.password
    or _seo_origin.path
    or _seo_origin.query
    or _seo_origin.fragment
):
    raise ImproperlyConfigured("SEO_SITE_URL must be a clean HTTPS origin.")
if (
    len(base.SECRET_KEY) < 50
    or len(set(base.SECRET_KEY)) < 5
    or base.SECRET_KEY.startswith("django-insecure-")
):
    raise ImproperlyConfigured(
        "DJANGO_SECRET_KEY must be a strong random key of at least 50 chars."
    )

_redis_urls = (
    ("REDIS_URL", base.REDIS_URL),
    ("CELERY_BROKER_URL", base.CELERY_BROKER_URL),
    ("CELERY_RESULT_BACKEND", base.CELERY_RESULT_BACKEND),
)
_redis_auth = None
for _setting_name, _redis_url in _redis_urls:
    _parsed_redis_url = urlsplit(_redis_url)
    if _parsed_redis_url.scheme not in {"redis", "rediss"} or not _parsed_redis_url.password:
        raise ImproperlyConfigured(f"{_setting_name} must use Redis authentication.")
    _current_auth = (_parsed_redis_url.username, _parsed_redis_url.password)
    if _redis_auth is None:
        _redis_auth = _current_auth
    elif _current_auth != _redis_auth:
        raise ImproperlyConfigured(
            "Redis, Celery broker, and result backend credentials must match."
        )

# Production must declare its hosts explicitly.
ALLOWED_HOSTS = base.env.list("DJANGO_ALLOWED_HOSTS")
CSRF_TRUSTED_ORIGINS = base.env.list("DJANGO_CSRF_TRUSTED_ORIGINS", default=[])
TRUST_X_REAL_IP = base.env.bool("DJANGO_TRUST_X_REAL_IP", default=False)
MIDDLEWARE = [*base.MIDDLEWARE, "apps.users.middleware.AdminLoginThrottleMiddleware"]

# Only enable this when the sole ingress proxy overwrites (rather than appends
# or passes through) the client's X-Forwarded-Proto header. Otherwise a client
# can make an insecure request appear secure to Django.
if base.env.bool("DJANGO_TRUST_X_FORWARDED_PROTO", default=False):
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SECURE_SSL_REDIRECT = base.env.bool("DJANGO_SECURE_SSL_REDIRECT", default=True)
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = "Lax"
CSRF_COOKIE_SAMESITE = "Lax"
# Roll out HSTS only after HTTPS is verified on the public domain. Enabling
# subdomains or preload additionally requires an audit of every subdomain.
SECURE_HSTS_SECONDS = base.env.int("DJANGO_SECURE_HSTS_SECONDS", default=0)
SECURE_HSTS_INCLUDE_SUBDOMAINS = base.env.bool(
    "DJANGO_SECURE_HSTS_INCLUDE_SUBDOMAINS", default=False
)
SECURE_HSTS_PRELOAD = base.env.bool("DJANGO_SECURE_HSTS_PRELOAD", default=False)
SECURE_CONTENT_TYPE_NOSNIFF = True
