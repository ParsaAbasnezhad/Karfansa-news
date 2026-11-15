"""Production settings: base + hardened security defaults."""

from config.settings import base

# Re-export base settings explicitly (no wildcard import).
globals().update({name: value for name, value in vars(base).items() if name.isupper()})

DEBUG = False
# Production must declare its hosts explicitly.
ALLOWED_HOSTS = base.env.list("DJANGO_ALLOWED_HOSTS")

SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SECURE_SSL_REDIRECT = base.env.bool("DJANGO_SECURE_SSL_REDIRECT", default=True)
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = base.env.int("DJANGO_SECURE_HSTS_SECONDS", default=31536000)
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_CONTENT_TYPE_NOSNIFF = True
