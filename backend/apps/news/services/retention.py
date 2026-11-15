from datetime import timedelta

from django.db.models import Q
from django.utils import timezone

from apps.news.models import News

NEWS_RETENTION_DAYS = 35


def retention_cutoff():
    return timezone.now() - timedelta(days=NEWS_RETENTION_DAYS)


def expired_news_queryset(cutoff=None):
    """Expire by publication time, using actual fetch time only when publication is absent."""
    cutoff = cutoff or retention_cutoff()
    return News.objects.filter(
        Q(published_at__lt=cutoff) | Q(published_at__isnull=True, fetched_at__lt=cutoff)
    )


def cleanup_expired_news(*, dry_run=False):
    expired = expired_news_queryset()
    count = expired.count()
    if not dry_run and count:
        expired.delete()
    return count
