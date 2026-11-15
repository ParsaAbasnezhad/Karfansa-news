from datetime import timedelta
from io import StringIO

import pytest
from django.conf import settings
from django.core.management import call_command
from django.utils import timezone
from django_celery_beat.models import PeriodicTask
from django_celery_beat.schedulers import DatabaseScheduler

from apps.news.models import News, NewsSource
from apps.news.services.retention import cleanup_expired_news
from apps.news.source_catalog import SOURCE_CATALOG
from config.celery import app as celery_app


@pytest.mark.django_db
def test_source_seed_is_idempotent_and_does_not_reactivate_admin_disabled_sources():
    output = StringIO()
    call_command("seed_news_sources", stdout=output)
    seeded = list(NewsSource.objects.filter(rss_url__in=[s["rss_url"] for s in SOURCE_CATALOG]))
    assert len(seeded) == 3
    assert all(source.is_active for source in seeded)
    assert {source.category for source in seeded} == {
        NewsSource.Category.ECONOMY,
        NewsSource.Category.OTHER,
    }

    seeded[0].is_active = False
    seeded[0].save(update_fields=["is_active"])
    call_command("seed_news_sources", stdout=StringIO())

    assert (
        NewsSource.objects.filter(rss_url__in=[s["rss_url"] for s in SOURCE_CATALOG]).count() == 3
    )
    seeded[0].refresh_from_db()
    assert seeded[0].is_active is False
    legacy_tasnim = NewsSource.objects.get(rss_url="https://www.tasnimnews.com/fa/rss/feed/0/8/0/")
    assert legacy_tasnim.is_active is False
    assert legacy_tasnim.last_fetch_status == "failed"


@pytest.mark.django_db
def test_35_day_retention_uses_publish_time_and_fetch_time_only_when_publish_date_is_missing():
    source = NewsSource.objects.create(name="منبع", rss_url="https://example.test/rss")
    now = timezone.now()
    News.objects.create(
        source=source,
        title="خبر قدیمی با تاریخ انتشار",
        original_url="https://example.test/old-published",
        published_at=now - timedelta(days=36),
    )
    old_unknown_date = News.objects.create(
        source=source,
        title="خبر قدیمی بدون تاریخ انتشار",
        original_url="https://example.test/old-unknown",
        published_at=None,
    )
    News.objects.filter(pk=old_unknown_date.pk).update(fetched_at=now - timedelta(days=36))
    recent = News.objects.create(
        source=source,
        title="خبر تازه",
        original_url="https://example.test/recent",
        published_at=now - timedelta(days=34),
    )

    assert cleanup_expired_news(dry_run=True) == 2
    assert News.objects.count() == 3
    assert cleanup_expired_news() == 2
    assert list(News.objects.values_list("pk", flat=True)) == [recent.pk]


def test_celery_schedules_rss_every_15_minutes_and_discovers_tasks():
    rss_schedule = settings.CELERY_BEAT_SCHEDULE["fetch-rss-news-every-15-minutes"]
    assert rss_schedule["schedule"] == 900
    assert "cleanup-news-daily" in settings.CELERY_BEAT_SCHEDULE

    celery_app.autodiscover_tasks(force=True)
    assert "apps.news.fetch_rss_news" in celery_app.tasks
    assert "apps.news.cleanup_old_news" in celery_app.tasks


@pytest.mark.django_db
def test_database_beat_scheduler_persists_the_15_minute_rss_schedule():
    scheduler = DatabaseScheduler(app=celery_app, lazy=True)
    scheduler.setup_schedule()

    task = PeriodicTask.objects.get(name="fetch-rss-news-every-15-minutes")
    assert task.task == "apps.news.fetch_rss_news"
    assert task.enabled is True
    assert task.interval.every == 900
    assert task.interval.period == "seconds"
