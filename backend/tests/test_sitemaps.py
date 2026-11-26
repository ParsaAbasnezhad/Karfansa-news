"""Search XML must reflect actual public, canonical editorial records."""

# ruff: noqa: S314 - these tests parse XML generated in-process by our own views.

from datetime import timedelta
from types import SimpleNamespace
from urllib.parse import quote
from xml.etree import ElementTree as ET

import pytest
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import Client
from django.utils import timezone

from apps.editorial.models import EditorialArticle, EditorialCategory
from apps.news.admin import archive_news
from apps.news.models import News, NewsSource, NewsTopic

SITEMAP_NS = "http://www.sitemaps.org/schemas/sitemap/0.9"
NEWS_NS = "http://www.google.com/schemas/sitemap-news/0.9"


def _locations(response) -> list[str]:
    root = ET.fromstring(response.content)
    return [item.text or "" for item in root.findall(f".//{{{SITEMAP_NS}}}loc")]


def _article(title: str, **kwargs) -> EditorialArticle:
    return EditorialArticle.objects.create(
        title=title,
        summary="A real summary",
        content="<p>A real article body.</p>",
        **kwargs,
    )


@pytest.mark.django_db
def test_regular_sitemap_filters_public_canonical_records_and_refreshes(client: Client) -> None:
    cache.clear()
    now = timezone.now()
    category = EditorialCategory.objects.create(name="اقتصاد")
    author = get_user_model().objects.create_user(
        username="writer", first_name="Actual", last_name="Writer"
    )
    initial = client.get("/sitemap.xml")
    assert initial.status_code == 200
    assert "https://karfansa.news.ir/" in _locations(initial)
    assert "https://karfansa.news.ir/news" not in _locations(initial)
    assert "https://karfansa.news.ir/editorial" not in _locations(initial)

    public = _article(
        "Published story",
        status=EditorialArticle.Status.PUBLISHED,
        published_at=now - timedelta(hours=2),
        author=author,
        category=category,
    )
    _article("Draft story")
    _article(
        "Future story",
        status=EditorialArticle.Status.PUBLISHED,
        published_at=now + timedelta(days=1),
    )
    _article(
        "No index story",
        status=EditorialArticle.Status.PUBLISHED,
        published_at=now - timedelta(hours=1),
        seo_noindex=True,
    )
    canonical_target = _article(
        "Canonical target",
        status=EditorialArticle.Status.PUBLISHED,
        published_at=now - timedelta(hours=3),
    )
    _article(
        "Canonical elsewhere",
        status=EditorialArticle.Status.PUBLISHED,
        published_at=now - timedelta(hours=1),
        seo_canonical_url=f"https://karfansa.news.ir/editorial/{canonical_target.slug}",
    )

    refreshed = client.get("/sitemap.xml")
    locations = _locations(refreshed)
    assert f"https://karfansa.news.ir/editorial/{quote(public.slug, safe='')}" in locations
    assert "https://karfansa.news.ir/editorial" in locations
    category_path = f"/editorial/category/{quote(category.slug, safe='')}"
    assert f"https://karfansa.news.ir{category_path}" in locations
    assert client.get(category_path).status_code == 200
    assert f"https://karfansa.news.ir/authors/{author.pk}" in locations
    root = ET.fromstring(refreshed.content)
    category_entry = next(
        entry
        for entry in root.findall(f"{{{SITEMAP_NS}}}url")
        if entry.findtext(f"{{{SITEMAP_NS}}}loc") == f"https://karfansa.news.ir{category_path}"
    )
    author_entry = next(
        entry
        for entry in root.findall(f"{{{SITEMAP_NS}}}url")
        if entry.findtext(f"{{{SITEMAP_NS}}}loc") == f"https://karfansa.news.ir/authors/{author.pk}"
    )
    assert category_entry.findtext(f"{{{SITEMAP_NS}}}lastmod") is None
    assert author_entry.findtext(f"{{{SITEMAP_NS}}}lastmod") == public.updated_at.isoformat()
    assert all("draft-story" not in url for url in locations)
    assert all("future-story" not in url for url in locations)
    assert all("no-index-story" not in url for url in locations)
    assert all("canonical-elsewhere" not in url for url in locations)
    assert refreshed["Content-Type"].startswith("application/xml")


@pytest.mark.django_db
def test_news_sitemap_uses_two_day_original_editorial_window(client: Client) -> None:
    cache.clear()
    now = timezone.now()
    author = get_user_model().objects.create_user(username="news_writer", first_name="Real")
    original = _article(
        "Original report",
        status=EditorialArticle.Status.PUBLISHED,
        published_at=now - timedelta(hours=1),
        author=author,
    )
    _article(
        "Attributed report",
        source_url="https://publisher.example/story",
        status=EditorialArticle.Status.PUBLISHED,
        published_at=now - timedelta(hours=1),
        author=author,
    )
    _article(
        "Attributed source name",
        source_name="Another Publisher",
        status=EditorialArticle.Status.PUBLISHED,
        published_at=now - timedelta(hours=1),
        author=author,
    )
    _article(
        "Old report",
        status=EditorialArticle.Status.PUBLISHED,
        published_at=now - timedelta(days=3),
        author=author,
    )
    _article(
        "Hidden report",
        status=EditorialArticle.Status.PUBLISHED,
        published_at=now - timedelta(hours=1),
        seo_noindex=True,
        author=author,
    )
    response = client.get("/news-sitemap.xml")
    root = ET.fromstring(response.content)
    locations = _locations(response)
    assert locations == [f"https://karfansa.news.ir/editorial/{quote(original.slug, safe='')}"]
    assert root.find(f".//{{{NEWS_NS}}}publication_date").text == original.published_at.isoformat()
    assert root.find(f".//{{{NEWS_NS}}}language").text == "fa"
    assert root.find(f".//{{{NEWS_NS}}}name").text == "کارفنسا نیوز"


@pytest.mark.django_db
def test_large_sitemaps_split_without_dropping_or_duplicating_urls(
    client: Client, monkeypatch: pytest.MonkeyPatch
) -> None:
    from apps.editorial import sitemap

    cache.clear()
    monkeypatch.setattr(sitemap, "CHUNK_SIZE", 3)
    monkeypatch.setattr(sitemap, "NEWS_CHUNK_SIZE", 2)
    now = timezone.now()
    author = get_user_model().objects.create_user(username="chunk_writer", first_name="Real")
    for number in range(4):
        _article(
            f"Report {number}",
            status=EditorialArticle.Status.PUBLISHED,
            published_at=now - timedelta(minutes=number + 1),
            author=author,
        )

    regular_index = _locations(client.get("/sitemap.xml"))
    assert len(regular_index) == 4  # two static and two editorial chunks
    regular_urls = []
    for index_url in regular_index:
        path = index_url.removeprefix("https://karfansa.news.ir")
        chunk = _locations(client.get(path))
        assert len(chunk) <= 3
        regular_urls.extend(chunk)
    assert len(regular_urls) == len(set(regular_urls)) == 9

    news_index = _locations(client.get("/news-sitemap.xml"))
    assert len(news_index) == 2
    news_urls = []
    for index_url in news_index:
        path = index_url.removeprefix("https://karfansa.news.ir")
        chunk = _locations(client.get(path))
        assert len(chunk) <= 2
        news_urls.extend(chunk)
    assert len(news_urls) == len(set(news_urls)) == 4


@pytest.mark.django_db
def test_news_listing_enters_and_leaves_sitemap_with_public_rss(client: Client) -> None:
    cache.clear()
    assert "https://karfansa.news.ir/news" not in _locations(client.get("/sitemap.xml"))
    source = NewsSource.objects.create(name="Real Publisher", rss_url="https://example.com/rss")
    topic = NewsTopic.objects.create(name="Economy", keywords=["economy"])
    item = News.objects.create(
        source=source,
        topic=topic,
        title="Publisher headline",
        original_url="https://example.com/story",
        score=1,
        is_published=True,
    )
    assert "https://karfansa.news.ir/news" in _locations(client.get("/sitemap.xml"))
    assert f"https://karfansa.news.ir/news/{item.pk}" not in _locations(client.get("/sitemap.xml"))

    model_admin = SimpleNamespace(message_user=lambda *args: None)
    archive_news(model_admin, None, News.objects.filter(pk=item.pk))
    assert "https://karfansa.news.ir/news" not in _locations(client.get("/sitemap.xml"))


def test_robots_points_to_both_canonical_sitemaps(client: Client) -> None:
    response = client.get("/robots.txt")
    text = response.content.decode()
    assert response.status_code == 200
    assert "Disallow: /admin/" in text
    assert "Sitemap: https://karfansa.news.ir/sitemap.xml" in text
    assert "Sitemap: https://karfansa.news.ir/news-sitemap.xml" in text


@pytest.mark.parametrize(
    "path",
    [
        "/news/",
        "/news/12/",
        "/editorial/",
        "/editorial/category/اقتصاد/",
        "/editorial/story/",
        "/authors/2/",
        "/about/",
        "/contact/",
    ],
)
def test_public_trailing_slash_redirect_preserves_query(client: Client, path: str) -> None:
    response = client.get(path, {"page": "2"})
    assert response.status_code == 301
    assert response["Location"] == f"{quote(path.rstrip('/'))}?page=2"
