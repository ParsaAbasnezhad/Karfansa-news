"""Development settings: base + debug-friendly overrides."""

from config.settings import base

# Re-export base settings explicitly (no wildcard import).
globals().update({name: value for name, value in vars(base).items() if name.isupper()})

DEBUG = True
ALLOWED_HOSTS = base.env.list("DJANGO_ALLOWED_HOSTS", default=["localhost", "127.0.0.1", "backend"])
