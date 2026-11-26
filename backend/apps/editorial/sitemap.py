"""Canonical, database-backed sitemaps for public Karfansa pages."""

import logging
import math
import uuid
from collections.abc import Callable
from datetime import datetime, timedelta
from typing import cast
from urllib.parse import quote
from xml.etree import ElementTree as ET

from django.conf import settings
from django.core.cache import cache
from django.db.models import Max, Q, QuerySet, Value
from django.db.models.functions import Concat, Trim
from django.http import Http404, HttpRequest, HttpResponse
from django.utils import timezone

from apps.news.selectors import list_rss_news
from apps.pages.models import AboutPage, ContactPage

from .models import EditorialArticle, EditorialCategory

logger = logging.getLogger(__name__)
SITEMAP_NS = "http://www.sitemaps.org/schemas/sitemap/0.9"
NEWS_NS = "http://www.google.com/schemas/sitemap-news/0.9"
CHUNK_SIZE = 10_000
NEWS_CHUNK_SIZE = 1_000
VERSION_KEY = "seo:sitemap:version"

ET.register_namespace("", SITEMAP_NS)
ET.register_namespace("news", NEWS_NS)


def _url(path: str) -> str:
    origin = str(getattr(settings, "SEO_SITE_URL", "https://karfansa.news.ir")).rstrip("/")
    return f"{origin}{path}"


def _article_path(slug: str) -> str:
    return f"/editorial/{quote(slug, safe='')}"


def _published_articles() -> QuerySet[EditorialArticle]:
    return EditorialArticle.objects.filter(
        status=EditorialArticle.Status.PUBLISHED,
        published_at__isnull=False,
        published_at__lte=timezone.now(),
        seo_noindex=False,
        seo_canonical_url="",
    )


def _news_articles() -> QuerySet[EditorialArticle]:
    """Only recent original reporting, not RSS or sourced rewrites."""
    return _published_articles().filter(
        published_at__gte=timezone.now() - timedelta(days=2),
        source_name="",
        source_url="",
    )


def _categories() -> QuerySet[EditorialCategory, tuple[str, datetime]]:
    visible = Q(
        articles__status=EditorialArticle.Status.PUBLISHED,
        articles__published_at__lte=timezone.now(),
        articles__seo_noindex=False,
        articles__seo_canonical_url="",
    )
    return (
        EditorialCategory.objects.filter(is_active=True, seo_noindex=False, seo_canonical_url="")
        .annotate(public_lastmod=Max("articles__updated_at", filter=visible))
        .filter(public_lastmod__isnull=False)
        .order_by("position", "id")
        .values_list("slug", "public_lastmod")
    )


def _authors() -> QuerySet[EditorialArticle, tuple[int, datetime]]:
    return (
        _published_articles()
        .filter(author_id__isnull=False)
        .annotate(full_name=Trim(Concat("author__first_name", Value(" "), "author__last_name")))
        .exclude(full_name="")
        .values("author_id")
        .annotate(public_lastmod=Max("updated_at"))
        .order_by("author_id")
        .values_list("author_id", "public_lastmod")
    )


def invalidate_sitemaps() -> None:
    """Rotate cache keys when published content or taxonomy changes."""
    try:
        cache.set(VERSION_KEY, uuid.uuid4().hex, timeout=None)
    except Exception:
        logger.exception("Could not invalidate sitemap cache")


def _version() -> str:
    try:
        return str(cache.get(VERSION_KEY, "0"))
    except Exception:
        logger.exception("Sitemap cache unavailable")
        return uuid.uuid4().hex


def _cached_xml(key: str, timeout: int, build: Callable[[], bytes]) -> HttpResponse:
    cache_key = f"seo:sitemap:{_version()}:{key}"
    xml = None
    try:
        xml = cache.get(cache_key)
    except Exception:
        logger.exception("Sitemap cache read failed")
    if xml is None:
        xml = build()
        try:
            cache.set(cache_key, xml, timeout=timeout)
        except Exception:
            logger.exception("Sitemap cache write failed")
    response = HttpResponse(xml, content_type="application/xml; charset=utf-8")
    response["Cache-Control"] = f"public, max-age={timeout}"
    return response


def _xml(root: ET.Element) -> bytes:
    return cast(bytes, ET.tostring(root, encoding="utf-8", xml_declaration=True))


def _entry(root: ET.Element, path: str, lastmod: datetime | None = None) -> ET.Element:
    item = ET.SubElement(root, f"{{{SITEMAP_NS}}}url")
    ET.SubElement(item, f"{{{SITEMAP_NS}}}loc").text = _url(path)
    if lastmod is not None:
        ET.SubElement(item, f"{{{SITEMAP_NS}}}lastmod").text = lastmod.isoformat()
    return item


def _static_counts(article_count: int | None = None) -> tuple[int, int, bool, bool]:
    return (
        _categories().count(),
        _authors().count(),
        list_rss_news().exists(),
        bool(article_count) if article_count is not None else _published_articles().exists(),
    )


def _static_entries(
    root: ET.Element,
    start: int,
    stop: int,
    category_count: int,
    include_news: bool,
    include_editorial: bool,
) -> None:
    fixed_count = 3 + include_news + include_editorial
    about = (
        AboutPage.objects.filter(pk=1).values_list("updated_at", flat=True).first()
        if start < fixed_count
        else None
    )
    contact = (
        ContactPage.objects.filter(pk=1).values_list("updated_at", flat=True).first()
        if start < fixed_count
        else None
    )
    fixed = [("/", None)]
    if include_news:
        fixed.append(("/news", None))
    if include_editorial:
        fixed.append(("/editorial", None))
    fixed.extend((("/about", about), ("/contact", contact)))
    for path, lastmod in fixed[start:stop]:
        _entry(root, path, lastmod)
    if stop <= len(fixed):
        return
    category_start = max(0, start - len(fixed))
    category_stop = max(0, stop - len(fixed))
    if category_stop > category_start:
        for slug, _lastmod in _categories()[category_start:category_stop].iterator(chunk_size=1000):
            _entry(root, f"/editorial/category/{quote(slug, safe='')}")
    author_start = max(0, start - len(fixed) - category_count)
    author_stop = max(0, stop - len(fixed) - category_count)
    if author_stop > author_start:
        for author_id, lastmod in _authors()[author_start:author_stop].iterator(chunk_size=1000):
            _entry(root, f"/authors/{author_id}", lastmod)


def _article_entries(root: ET.Element, start: int, stop: int) -> None:
    articles = (
        _published_articles()
        .order_by("-published_at", "-id")
        .values_list("slug", "updated_at")[start:stop]
    )
    for slug, updated_at in articles.iterator(chunk_size=1000):
        _entry(root, _article_path(slug), updated_at)


def _urlset(
    *,
    static_start: int = 0,
    static_stop: int = 0,
    category_count: int = 0,
    include_news: bool = False,
    include_editorial: bool = False,
    article_start: int = 0,
    article_stop: int = 0,
) -> bytes:
    root = ET.Element(f"{{{SITEMAP_NS}}}urlset")
    if static_stop > static_start:
        _static_entries(
            root, static_start, static_stop, category_count, include_news, include_editorial
        )
    if article_stop > article_start:
        _article_entries(root, article_start, article_stop)
    return _xml(root)


def _index(paths: list[str]) -> bytes:
    root = ET.Element(f"{{{SITEMAP_NS}}}sitemapindex")
    for path in paths:
        item = ET.SubElement(root, f"{{{SITEMAP_NS}}}sitemap")
        ET.SubElement(item, f"{{{SITEMAP_NS}}}loc").text = _url(path)
    return _xml(root)


def editorial_sitemap(request: HttpRequest) -> HttpResponse:
    def build() -> bytes:
        article_count = _published_articles().count()
        category_count, author_count, include_news, include_editorial = _static_counts(
            article_count
        )
        static_count = 3 + include_news + include_editorial + category_count + author_count
        if static_count + article_count <= CHUNK_SIZE:
            return _urlset(
                static_stop=static_count,
                category_count=category_count,
                include_news=include_news,
                include_editorial=include_editorial,
                article_stop=article_count,
            )
        paths = [
            f"/sitemaps/static-{page}.xml"
            for page in range(1, math.ceil(static_count / CHUNK_SIZE) + 1)
        ]
        paths.extend(
            f"/sitemaps/editorial-{page}.xml"
            for page in range(1, math.ceil(article_count / CHUNK_SIZE) + 1)
        )
        return _index(paths)

    return _cached_xml("regular", 300, build)


def static_sitemap_page(request: HttpRequest, page: int) -> HttpResponse:
    category_count, author_count, include_news, include_editorial = _static_counts()
    count = 3 + include_news + include_editorial + category_count + author_count
    if page < 1 or page > math.ceil(count / CHUNK_SIZE):
        raise Http404
    start = (page - 1) * CHUNK_SIZE
    return _cached_xml(
        f"static:{page}",
        300,
        lambda: _urlset(
            static_start=start,
            static_stop=start + CHUNK_SIZE,
            category_count=category_count,
            include_news=include_news,
            include_editorial=include_editorial,
        ),
    )


def editorial_sitemap_page(request: HttpRequest, page: int) -> HttpResponse:
    count = _published_articles().count()
    if page < 1 or page > math.ceil(count / CHUNK_SIZE):
        raise Http404
    start = (page - 1) * CHUNK_SIZE
    return _cached_xml(
        f"editorial:{page}",
        300,
        lambda: _urlset(article_start=start, article_stop=start + CHUNK_SIZE),
    )


def _news_urlset(start: int, stop: int) -> bytes:
    root = ET.Element(f"{{{SITEMAP_NS}}}urlset")
    rows = (
        _news_articles()
        .order_by("-published_at", "-id")
        .values_list("slug", "title", "published_at")[start:stop]
    )
    for slug, title, published_at in rows.iterator(chunk_size=1000):
        if published_at is None:
            continue
        item = _entry(root, _article_path(slug))
        news = ET.SubElement(item, f"{{{NEWS_NS}}}news")
        publication = ET.SubElement(news, f"{{{NEWS_NS}}}publication")
        ET.SubElement(publication, f"{{{NEWS_NS}}}name").text = "کارفنسا نیوز"
        ET.SubElement(publication, f"{{{NEWS_NS}}}language").text = "fa"
        ET.SubElement(news, f"{{{NEWS_NS}}}publication_date").text = published_at.isoformat()
        ET.SubElement(news, f"{{{NEWS_NS}}}title").text = title
    return _xml(root)


def news_sitemap(request: HttpRequest) -> HttpResponse:
    def build() -> bytes:
        count = _news_articles().count()
        if count <= NEWS_CHUNK_SIZE:
            return _news_urlset(0, NEWS_CHUNK_SIZE)
        paths = [
            f"/sitemaps/news-{page}.xml"
            for page in range(1, math.ceil(count / NEWS_CHUNK_SIZE) + 1)
        ]
        return _index(paths)

    return _cached_xml("news", 60, build)


def news_sitemap_page(request: HttpRequest, page: int) -> HttpResponse:
    count = _news_articles().count()
    if page < 1 or page > math.ceil(count / NEWS_CHUNK_SIZE):
        raise Http404
    start = (page - 1) * NEWS_CHUNK_SIZE
    return _cached_xml(f"news:{page}", 60, lambda: _news_urlset(start, start + NEWS_CHUNK_SIZE))


def robots_txt(request: HttpRequest) -> HttpResponse:
    paths = (
        "/admin/",
        "/api/",
        "/account/",
        "/login",
        "/register",
        "/verify",
        "/forgot-password",
        "/reset-password",
    )
    lines = ["User-agent: *", "Allow: /", *(f"Disallow: {path}" for path in paths)]
    lines.extend((f"Sitemap: {_url('/sitemap.xml')}", f"Sitemap: {_url('/news-sitemap.xml')}", ""))
    response = HttpResponse("\n".join(lines), content_type="text/plain; charset=utf-8")
    response["Cache-Control"] = "public, max-age=300"
    return response
