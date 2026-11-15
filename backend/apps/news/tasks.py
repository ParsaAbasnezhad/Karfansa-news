"""Background tasks for editorial news."""

from celery import shared_task
from django.db import DatabaseError

from apps.news.services.retention import cleanup_expired_news
from apps.news.services.rss_fetcher import fetch_all_sources


@shared_task(
    name="apps.news.fetch_rss_news",
    autoretry_for=(DatabaseError,),
    retry_backoff=True,
    retry_backoff_max=300,
    retry_jitter=True,
    max_retries=5,
    acks_late=True,
    reject_on_worker_lost=True,
)
def fetch_rss_news() -> list[dict[str, object]]:
    """Fetch and filter configured RSS feeds for public news listings."""
    return fetch_all_sources()


@shared_task(
    name="apps.news.cleanup_old_news",
    autoretry_for=(DatabaseError,),
    retry_backoff=True,
    retry_backoff_max=300,
    retry_jitter=True,
    max_retries=5,
)
def cleanup_old_news() -> int:
    """Remove articles outside the published/fetched 35-day retention window."""
    return cleanup_expired_news()
