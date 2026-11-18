"""Isolated settings for fast local tests without PostgreSQL or Redis."""

import os

os.environ.setdefault("DJANGO_SECRET_KEY", "test-only-not-for-deployment")
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/15")

from config.settings import base

globals().update({name: value for name, value in vars(base).items() if name.isupper()})

DEBUG = True
ALLOWED_HOSTS = ["testserver", "localhost", "127.0.0.1"]
DATABASES = {"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}}
CACHES = {"default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"}}
EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"
CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True
AUTH_PUBLIC_RESPONSE_FLOOR_SECONDS = 0
SMS_PROVIDER_CLASS = ""
SMS_DEV_INBOX = ""
KAVENEGAR_API_KEY = ""
KAVENEGAR_VERIFY_TEMPLATE = ""
KAVENEGAR_SENDER = ""
