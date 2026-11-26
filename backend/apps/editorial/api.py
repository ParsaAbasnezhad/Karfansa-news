"""Read-only public API for Karfansa's own reporting."""

import hashlib
import logging
import re
from math import ceil
from urllib.parse import urlsplit

from django.core.cache import cache
from django.db.models import F
from django.http import HttpRequest
from ninja import Query, Router

from apps.common.client_ip import client_ip
from apps.common.exceptions import AppError, NotFoundError

from . import selectors
from .models import EditorialArticle, EditorialCategory, EditorialImage
from .sanitizer import sanitize_article_html
from .schemas import (
    ArticleDetailResponse,
    ArticleListOut,
    CategoriesOut,
    FeaturedOut,
    LatestOut,
)
from .seo import effective_canonical_url

router = Router()
logger = logging.getLogger(__name__)
BOT_USER_AGENT = re.compile(r"bot|crawler|spider|slurp|preview", re.IGNORECASE)


def _image_url(request: HttpRequest, image) -> str:
    return image.url if image else ""


def _srcset(image, variants: dict[str, str]) -> str:
    if not image:
        return ""
    return ", ".join(
        f"{image.storage.url(path)} {width}w"
        for width, path in sorted(variants.items(), key=lambda item: int(item[0]))
    )


def _person_name(person) -> str:
    return person.get_full_name().strip() if person else ""


def _source_url(value: str) -> str:
    parsed = urlsplit(value.strip())
    return value if parsed.scheme.lower() in {"http", "https"} and parsed.netloc else ""


def _category(category: EditorialCategory | None) -> dict[str, object] | None:
    if category is None:
        return None
    canonical_override = effective_canonical_url(
        category.seo_canonical_url, kind="category", own_slug=category.slug
    )
    return {
        "id": category.pk,
        "slug": category.slug,
        "name": category.name,
        "seo_title": category.seo_title,
        "seo_description": category.seo_description,
        "seo_social_image_url": category.seo_social_image.url if category.seo_social_image else "",
        "seo_noindex": category.seo_noindex
        or bool(category.seo_canonical_url and not canonical_override),
        "seo_canonical_url": canonical_override,
    }


def _article(request: HttpRequest, item: EditorialArticle) -> dict[str, object]:
    return {
        "id": item.pk,
        "slug": item.slug,
        "title": item.title,
        "summary": item.summary,
        "source_url": _source_url(item.source_url),
        "featured_image_url": _image_url(request, item.featured_image),
        "featured_image_srcset": _srcset(item.featured_image, item.featured_image_variants),
        "featured_image_width": item.featured_image_width,
        "featured_image_height": item.featured_image_height,
        "category": _category(item.category),
        "tags": [tag.name for tag in item.tags.all()],
        "author_name": _person_name(item.author),
        "author_id": item.author_id if _person_name(item.author) else None,
        "published_at": item.published_at,
        "updated_at": item.updated_at,
        "reading_time": item.reading_time,
        "is_featured": item.is_featured,
        "is_breaking": item.is_breaking,
        "is_pinned": item.is_pinned,
        "priority": item.priority,
    }


def _gallery_image(request: HttpRequest, image: EditorialImage) -> dict[str, object]:
    return {
        "id": image.pk,
        "image_url": _image_url(request, image.image),
        "image_srcset": _srcset(image.image, image.variants),
        "width": image.width,
        "height": image.height,
        "alt_text": image.alt_text,
        "caption": image.caption,
    }


def _record_view(request: HttpRequest, item: EditorialArticle) -> None:
    agent = request.META.get("HTTP_USER_AGENT", "")
    if BOT_USER_AGENT.search(agent):
        return
    identity = (
        f"user:{request.user.pk}"
        if request.user.is_authenticated
        else f"{client_ip(request)}:{agent[:200]}"
    )
    digest = hashlib.sha256(
        f"{item.pk}:{item.created_at.isoformat()}:{identity}".encode()
    ).hexdigest()
    key = f"editorial:view:{digest}"
    try:
        if cache.add(key, True, timeout=24 * 60 * 60):
            EditorialArticle.objects.filter(pk=item.pk).update(view_count=F("view_count") + 1)
            item.view_count += 1
    except Exception:
        logger.exception("Could not record editorial view", extra={"article_id": item.pk})


@router.get("/", response=ArticleListOut, operation_id="editorial_list")
def list_editorial(
    request: HttpRequest,
    category: str = "",
    q: str = "",
    ordering: str = "-published_at",
    page: int = Query(1, ge=1),
    page_size: int = Query(12, ge=1, le=50),
) -> dict[str, object]:
    order = ordering.strip() or "-published_at"
    if order not in selectors.PUBLIC_ORDERING:
        raise AppError("مرتب‌سازی معتبر نیست.", details={"ordering": order})
    articles = selectors.list_articles(
        category=category.strip(), query=q.strip()[:200], ordering=order
    )
    count = articles.count()
    start = (page - 1) * page_size
    return {
        "results": [_article(request, item) for item in articles[start : start + page_size]],
        "categories": [_category(category) for category in selectors.list_categories()],
        "count": count,
        "page": page,
        "page_size": page_size,
        "total_pages": ceil(count / page_size) if count else 0,
    }


@router.get("/featured/", response=FeaturedOut, operation_id="editorial_featured")
def featured_editorial(request: HttpRequest) -> dict[str, object]:
    items = list(selectors.featured_articles()[:5])
    return {
        "featured": _article(request, items[0]) if items else None,
        "secondary": [_article(request, item) for item in items[1:]],
    }


@router.get("/latest/", response=LatestOut, operation_id="editorial_latest")
def latest_editorial(request: HttpRequest) -> dict[str, object]:
    items = selectors.public_articles().order_by("-published_at", "-id")[:12]
    return {"results": [_article(request, item) for item in items]}


@router.get("/categories/", response=CategoriesOut, operation_id="editorial_categories")
def editorial_categories(request: HttpRequest) -> dict[str, object]:
    return {"results": [_category(item) for item in selectors.list_categories()]}


@router.get("/{slug}/", response=ArticleDetailResponse, operation_id="editorial_detail")
def editorial_detail(request: HttpRequest, slug: str) -> dict[str, object]:
    item = selectors.public_articles().filter(slug=slug).first()
    if item is None:
        raise NotFoundError("خبر مورد نظر پیدا نشد.")
    _record_view(request, item)
    related = selectors.public_articles().exclude(pk=item.pk)
    if item.category_id:
        related = related.filter(category_id=item.category_id)
    related = related.order_by("-published_at", "-id")[:4]
    canonical_override = effective_canonical_url(
        item.seo_canonical_url, kind="article", own_slug=item.slug
    )
    return {
        "item": {
            **_article(request, item),
            "content": sanitize_article_html(item.content),
            "gallery": [_gallery_image(request, image) for image in item.gallery.all()],
            "editor_name": _person_name(item.editor),
            "source_name": item.source_name,
            "source_url": _source_url(item.source_url),
            "seo_title": item.seo_title,
            "seo_description": item.seo_description,
            "seo_social_image_url": _image_url(request, item.seo_social_image),
            "seo_noindex": item.seo_noindex
            or bool(item.seo_canonical_url and not canonical_override),
            "seo_canonical_url": canonical_override,
            "view_count": item.view_count,
        },
        "related": [_article(request, article) for article in related],
    }
