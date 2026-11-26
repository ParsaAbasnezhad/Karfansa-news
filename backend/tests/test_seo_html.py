"""Initial HTML must be useful and truthful without executing JavaScript."""

import json
import re
from datetime import timedelta
from urllib.parse import quote

import pytest
from django.contrib.auth import get_user_model
from django.test import Client
from django.utils import timezone

from apps.editorial.models import EditorialArticle, EditorialCategory
from apps.news.models import News, NewsSource, NewsTopic


def _graph(html: str) -> list[dict[str, object]]:
    match = re.search(r'<script id="seo-jsonld" type="application/ld\+json">(.*?)</script>', html)
    assert match is not None
    return json.loads(match.group(1))["@graph"]


@pytest.mark.django_db
def test_home_and_editorial_initial_html(client: Client) -> None:
    author = get_user_model().objects.create_user(
        username="reporter", first_name="Sara", last_name="Ahmadi"
    )
    category = EditorialCategory.objects.create(name="اقتصاد")
    item = EditorialArticle.objects.create(
        title="گزارش بازار امروز",
        summary="وضعیت بازار در امروز",
        content="<p>متن گزارش واقعی</p>",
        category=category,
        author=author,
        status=EditorialArticle.Status.PUBLISHED,
        published_at=timezone.now() - timedelta(hours=1),
    )
    path = f"/editorial/{quote(item.slug, safe='')}"

    home = client.get("/")
    assert home.status_code == 200
    home_html = home.content.decode()
    assert "گزارش بازار امروز" in home_html
    assert '<html lang="fa-IR" dir="rtl">' in home_html
    assert '<link rel="canonical" href="https://karfansa.news.ir/"' in home_html
    assert [node["@type"] for node in _graph(home_html)].count("WebSite") == 1

    story = client.get(path)
    assert story.status_code == 200
    html = story.content.decode()
    assert "متن گزارش واقعی" in html
    assert '<meta property="og:type" content="article"' in html
    assert f'<link rel="canonical" href="https://karfansa.news.ir{path}"' in html
    assert html.count('id="seo-jsonld"') == 1
    nodes = _graph(html)
    news_article = next(node for node in nodes if node["@type"] == "NewsArticle")
    assert news_article["headline"] == item.title
    assert news_article["author"]["url"] == f"https://karfansa.news.ir/authors/{author.pk}"
    assert client.get(f"/authors/{author.pk}").status_code == 200
    assert client.get(f"/editorial/category/{quote(category.slug, safe='')}").status_code == 200


@pytest.mark.django_db
def test_unpublished_and_archived_story_statuses(client: Client) -> None:
    draft = EditorialArticle.objects.create(title="Draft", summary="draft", content="<p>draft</p>")
    assert client.get(f"/editorial/{draft.slug}").status_code == 404
    draft.status = EditorialArticle.Status.ARCHIVED
    draft.save()
    assert client.get(f"/editorial/{draft.slug}").status_code == 410


@pytest.mark.django_db
def test_rss_detail_is_attributed_and_noindex(client: Client) -> None:
    source = NewsSource.objects.create(name="External Wire", rss_url="https://example.org/rss")
    topic = NewsTopic.objects.create(name="Economy")
    item = News.objects.create(
        source=source,
        topic=topic,
        title="External headline",
        summary="External summary",
        original_url="https://example.org/story",
        score=50,
        is_published=True,
    )
    response = client.get(f"/news/{item.pk}")
    assert response.status_code == 200
    html = response.content.decode()
    assert "External Wire" in html
    assert "https://example.org/story" in html
    assert 'name="robots" content="noindex,follow,max-image-preview:large"' in html
    assert not any(node["@type"] in {"NewsArticle", "Article"} for node in _graph(html))
    assert client.get("/news/999999").status_code == 404


@pytest.mark.django_db
def test_removed_canonical_target_does_not_leave_indexable_source(client: Client) -> None:
    published = timezone.now() - timedelta(hours=1)
    target = EditorialArticle.objects.create(
        title="Target",
        summary="Target summary",
        content="<p>Target body</p>",
        status=EditorialArticle.Status.PUBLISHED,
        published_at=published,
    )
    source = EditorialArticle.objects.create(
        title="Source",
        summary="Source summary",
        content="<p>Source body</p>",
        status=EditorialArticle.Status.PUBLISHED,
        published_at=published,
        seo_canonical_url=f"https://karfansa.news.ir/editorial/{target.slug}",
    )
    target.status = EditorialArticle.Status.ARCHIVED
    target.save()
    html = client.get(f"/editorial/{source.slug}").content.decode()
    assert '<meta name="robots" content="noindex,follow' in html
    assert f'<link rel="canonical" href="https://karfansa.news.ir/editorial/{source.slug}"' in html
    assert not any(node["@type"] == "NewsArticle" for node in _graph(html))
    api = client.get(f"/api/v1/editorial/{source.slug}/").json()["item"]
    assert api["seo_canonical_url"] == ""
    assert api["seo_noindex"] is True


@pytest.mark.django_db
def test_admin_seo_preview_renders_for_new_content(client: Client) -> None:
    admin = get_user_model().objects.create_superuser(
        username="seo-admin", password="test-password"
    )
    client.force_login(admin)
    for path in (
        "/admin/editorial/editorialarticle/add/",
        "/admin/editorial/editorialcategory/add/",
    ):
        response = client.get(path)
        assert response.status_code == 200
        assert b"editorial-seo-preview" in response.content


@pytest.mark.django_db
def test_redundant_self_canonical_is_normalized() -> None:
    category = EditorialCategory.objects.create(name="Industry")
    category.seo_canonical_url = f"https://karfansa.news.ir/editorial/category/{category.slug}"
    category.save()
    assert category.seo_canonical_url == ""

    item = EditorialArticle.objects.create(title="Story", summary="Summary", content="<p>Body</p>")
    item.seo_canonical_url = f"https://karfansa.news.ir/editorial/{item.slug}"
    item.save()
    assert item.seo_canonical_url == ""


@pytest.mark.django_db
def test_sourced_article_and_public_page_schema_are_truthful(client: Client) -> None:
    item = EditorialArticle.objects.create(
        title="Sourced analysis",
        summary="Analysis summary",
        content="<p>Analysis body</p>",
        source_name="External publisher",
        source_url="https://example.org/report",
        status=EditorialArticle.Status.PUBLISHED,
        published_at=timezone.now() - timedelta(hours=1),
    )
    html = client.get(f"/editorial/{item.slug}").content.decode()
    nodes = _graph(html)
    article = next(node for node in nodes if node["@type"] == "Article")
    assert article["isBasedOn"] == "https://example.org/report"
    assert "External publisher" in html
    assert not any(node["@type"] == "NewsArticle" for node in nodes)

    for path, schema_type in (("/about", "AboutPage"), ("/contact", "ContactPage")):
        response = client.get(path)
        assert response.status_code == 200
        assert any(node["@type"] == schema_type for node in _graph(response.content.decode()))
