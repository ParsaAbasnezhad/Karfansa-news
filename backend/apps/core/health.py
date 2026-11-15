"""Dependency probes used by the health endpoint."""

import logging

import redis
from django.conf import settings
from django.db import connection

logger = logging.getLogger(__name__)

CHECK_OK = "ok"
CHECK_FAILED = "unavailable"


def check_database() -> str:
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
    except Exception:
        logger.exception("Database health check failed")
        return CHECK_FAILED
    return CHECK_OK


def check_redis() -> str:
    try:
        client = redis.Redis.from_url(
            settings.REDIS_URL,  # type: ignore[misc]  # custom setting, unknown to django-stubs
            socket_connect_timeout=2,
            socket_timeout=2,
        )
        client.ping()
    except Exception:
        logger.exception("Redis health check failed")
        return CHECK_FAILED
    return CHECK_OK
