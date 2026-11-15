import json
from datetime import UTC, datetime, timedelta
from email.utils import format_datetime
from io import StringIO
from unittest.mock import patch

import pytest
import requests
from django.core.cache import cache
from django.core.management import call_command
from django.test import override_settings

from apps.news.models import News, NewsFetchRun, NewsIntake, NewsSource
from apps.news.services.rss_fetcher import fetch_all_sources, fetch_source

RSS = """<?xml version="1.0" encoding="UTF-8" ?>
<rss version="2.0">
<channel>
<title>sample</title>
<item>
<title>رشد صادرات پسته و تجارت کشاورزی</title>
<link>https://news.example/pistachio</link>
<description>صادرات پسته و تجارت کشاورزی بیشتر شد</description>
<enclosure url="https://cdn.example/pistachio.jpg" type="image/jpeg" />
</item>
<item>
<title>پیروزی تیم فوتبال در لیگ</title>
<link>https://news.example/sport</link>
<description>مسابقه ورزشی دیشب برگزار شد</description>
</item>
</channel>
</rss>
""".encode()

LOCMEM_CACHE = {
    "default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"},
}


@override_settings(CACHES=LOCMEM_CACHE)
@pytest.mark.django_db
def test_fetch_keeps_relevant_news_and_skips_reviewed_items():
    NewsSource.objects.update(is_active=False)
    broken = NewsSource.objects.create(
        name="خراب",
        rss_url="https://broken.example/rss.xml",
        is_active=True,
    )
    source = NewsSource.objects.create(
        name="اقتصادی",
        rss_url="https://news.example/rss.xml",
        website_url="https://news.example",
        is_active=True,
    )

    def download(url):
        if url == broken.rss_url:
            raise ValueError("feed unavailable")
        return RSS

    with patch("apps.news.services.rss_fetcher.download_feed", side_effect=download):
        first = fetch_all_sources()
        second = fetch_source(source)

    assert {item["source"] for item in first} == {"خراب", "اقتصادی"}
    failed = next(item for item in first if item["source"] == "خراب")
    saved = next(item for item in first if item["source"] == "اقتصادی")
    assert failed["status"] == "failed"
    assert saved["status"] == "success"
    assert saved["created"] == 1
    assert saved["saved"] == 1
    assert saved["rejected"] == 1

    broken.refresh_from_db()
    assert broken.last_fetch_status == "failed"
    assert broken.last_fetch_error
    assert broken.health_status == NewsSource.Health.UNHEALTHY
    assert broken.last_attempt_at is not None
    assert broken.last_error_count == 1

    story = News.objects.get(original_url="https://news.example/pistachio")
    assert story.topic is not None
    assert story.score > 0
    assert story.is_published is True
    assert story.published_at is None
    assert source.last_fetched_count == 2
    assert source.last_accepted_count == 0
    assert source.last_rejected_count == 0
    assert source.last_duplicate_count == 2
    assert source.health_status == NewsSource.Health.HEALTHY
    assert story.image_url == "https://cdn.example/pistachio.jpg"
    assert not News.objects.filter(original_url="https://news.example/sport").exists()
    rejected = NewsIntake.objects.get(
        original_url="https://news.example/sport",
        status=NewsIntake.Status.REJECTED,
    )
    assert "نامرتبط" in rejected.decision_reason

    assert second["created"] == 0
    assert second["skipped"] == 2
    assert second["duplicates"] == 2
    assert News.objects.filter(source=source).count() == 1


@pytest.mark.django_db
def test_guid_is_scoped_to_source_and_relative_links_are_resolved(client):
    rss = """<?xml version="1.0" encoding="UTF-8" ?>
    <rss version="2.0"><channel><title>sample</title><item>
    <title>رشد صادرات پسته و تجارت کشاورزی</title>
    <link>/story#comments</link><guid>shared-id</guid>
    <description>صادرات پسته و تجارت کشاورزی بیشتر شد</description>
    <pubDate>Tue, 10 Nov 2026 10:30:00 +0330</pubDate>
    <enclosure url="/cover.jpg" type="image/jpeg" />
    </item></channel></rss>""".encode()
    first = NewsSource.objects.create(name="یک", rss_url="https://one.example/feed.xml")
    second = NewsSource.objects.create(name="دو", rss_url="https://two.example/feed.xml")

    with patch("apps.news.services.rss_fetcher.download_feed", return_value=rss):
        assert fetch_source(first)["created"] == 1
        assert fetch_source(second)["created"] == 1
        duplicate = fetch_source(first)

    assert duplicate["duplicates"] == 1
    assert News.objects.filter(guid="shared-id").count() == 2
    story = News.objects.get(source=first)
    assert story.original_url == "https://one.example/story"
    assert story.image_url == "https://one.example/cover.jpg"
    assert story.published_at == datetime(2026, 11, 10, 7, 0, tzinfo=UTC)
    listing = client.get("/api/v1/news/", {"q": "رشد صادرات پسته"})
    assert listing.status_code == 200
    assert listing.json()["count"] == 2
    detail = client.get(f"/api/v1/news/{story.pk}/")
    assert detail.status_code == 200
    assert detail.json()["item"]["original_url"] == story.original_url


@override_settings(CACHES=LOCMEM_CACHE)
@pytest.mark.django_db
def test_partial_feed_reports_entry_errors():
    NewsSource.objects.update(is_active=False)
    source = NewsSource.objects.create(name="ناقص", rss_url="https://news.example/feed.xml")
    rss = """<?xml version="1.0" encoding="UTF-8" ?>
    <rss version="2.0"><channel><title>sample</title>
    <item><title>خبر نامعتبر</title><link>javascript:alert(1)</link></item>
    <item><title>رشد صادرات پسته و تجارت کشاورزی</title>
    <link>https://news.example/pistachio</link>
    <description>صادرات پسته و تجارت کشاورزی بیشتر شد</description></item>
    </channel></rss>""".encode()

    with patch("apps.news.services.rss_fetcher.download_feed", return_value=rss):
        result = fetch_all_sources()[0]

    source.refresh_from_db()
    assert result["status"] == "partial"
    assert result["fetched"] == 2
    assert result["created"] == 1
    assert result["errors"] == 1
    assert source.last_fetch_status == "partial"
    assert source.health_status == NewsSource.Health.DEGRADED
    run = NewsFetchRun.objects.get()
    assert run.status == NewsFetchRun.Status.PARTIAL
    assert run.started_at is not None
    assert run.finished_at is not None
    assert run.sources_checked == 1
    assert run.fetched_count == 2
    assert run.new_count == 1
    assert run.accepted_count == 1
    assert run.error_count == 1


@override_settings(CACHES=LOCMEM_CACHE)
@pytest.mark.django_db
def test_overlapping_fetch_skips_before_downloading():
    assert cache.add("news:rss-fetch-lock", "running", timeout=30)
    try:
        with patch("apps.news.services.rss_fetcher.download_feed") as download:
            result = fetch_all_sources()
        assert result[0]["status"] == "skipped"
        assert result[0]["reason"] == "RSS fetch is already running"
        assert result[0]["run_id"] is not None
        download.assert_not_called()
    finally:
        cache.delete("news:rss-fetch-lock")


@override_settings(CACHES=LOCMEM_CACHE)
@pytest.mark.django_db
def test_lock_backend_failure_is_recorded_as_a_failed_run():
    with (
        patch(
            "apps.news.services.rss_fetcher.cache.add",
            side_effect=RuntimeError("redis unavailable"),
        ),
        pytest.raises(RuntimeError),
    ):
        fetch_all_sources()

    run = NewsFetchRun.objects.get()
    assert run.status == NewsFetchRun.Status.FAILED
    assert run.error_count == 1
    assert run.finished_at is not None


def test_fetch_command_json_reports_all_counts():
    output = StringIO()
    result = {
        "source": "اقتصادی",
        "status": "partial",
        "fetched": 5,
        "accepted": 2,
        "created": 2,
        "saved": 2,
        "rejected": 1,
        "skipped": 1,
        "duplicates": 1,
        "errors": 1,
    }
    with patch("apps.news.management.commands.fetch_news.fetch_all_sources", return_value=[result]):
        call_command("fetch_news", "--json", stdout=output)

    payload = json.loads(output.getvalue())
    assert payload["totals"]["sources"] == 1
    assert payload["totals"]["partial_sources"] == 1
    assert payload["totals"]["fetched"] == 5
    assert payload["totals"]["saved"] == 2
    assert payload["totals"]["new_articles"] == 2
    assert payload["totals"]["duplicates"] == 1


@override_settings(CACHES=LOCMEM_CACHE)
@pytest.mark.django_db
def test_transient_network_errors_retry_with_exponential_backoff():
    NewsSource.objects.update(is_active=False)
    source = NewsSource.objects.create(name="اقتصادی", rss_url="https://news.example/rss.xml")
    with (
        patch(
            "apps.news.services.rss_fetcher.download_feed",
            side_effect=[requests.ConnectionError("temporary"), requests.Timeout(), RSS],
        ) as download,
        patch("apps.news.services.rss_fetcher.time.sleep") as sleep,
    ):
        result = fetch_source(source)

    assert result["saved"] == 1
    assert download.call_count == 3
    assert [call.args[0] for call in sleep.call_args_list] == [1, 2]


@override_settings(CACHES=LOCMEM_CACHE)
@pytest.mark.django_db
def test_news_older_than_retention_window_is_rejected_without_changing_its_date():
    NewsSource.objects.update(is_active=False)
    source = NewsSource.objects.create(name="اقتصادی", rss_url="https://news.example/rss.xml")
    old_date = datetime.now(UTC) - timedelta(days=45)
    rss = f"""<?xml version="1.0" encoding="UTF-8" ?>
    <rss version="2.0"><channel><title>sample</title><item>
    <title>رشد صادرات پسته و تجارت کشاورزی</title>
    <link>https://news.example/old</link>
    <description>صادرات پسته و تجارت کشاورزی بیشتر شد</description>
    <pubDate>{format_datetime(old_date)}</pubDate>
    </item></channel></rss>""".encode()

    with patch("apps.news.services.rss_fetcher.download_feed", return_value=rss):
        result = fetch_source(source)

    assert result["rejected"] == 1
    assert not News.objects.filter(original_url="https://news.example/old").exists()
    intake = NewsIntake.objects.get(original_url="https://news.example/old")
    assert intake.status == NewsIntake.Status.REJECTED
    assert "35" in intake.decision_reason
