"""Validation for editorial canonical overrides.

Overrides are deliberately limited to real public pages of the same content
type. This prevents an admin typo from advertising an off-site or dead URL as
the canonical version of a story.
"""

import re
from urllib.parse import unquote, urlsplit

from django.conf import settings
from django.core.exceptions import ValidationError
from django.utils import timezone


def canonical_path(value: str, *, kind: str) -> str:
    """Return the decoded path of a safe canonical URL or raise ValidationError."""
    if not value:
        return ""
    try:
        parsed = urlsplit(value)
        site = urlsplit(getattr(settings, "SEO_SITE_URL", "https://karfansa.news.ir"))
        parsed_port = parsed.port
    except ValueError as exc:
        raise ValidationError("آدرس کنونیکال معتبر نیست.") from exc
    if (
        parsed.scheme != "https"
        or parsed.netloc != site.netloc
        or parsed.username is not None
        or parsed.password is not None
        or parsed_port is not None
        or parsed.query
        or parsed.fragment
        or not parsed.path.startswith("/")
        or parsed.path.startswith("//")
        or re.search(r"%(?:2f|5c|3f|23|25)", parsed.path, re.IGNORECASE)
    ):
        raise ValidationError("آدرس کنونیکال باید HTTPS و در دامنه رسمی و بدون پارامتر باشد.")
    path = unquote(parsed.path)
    prefix = "/editorial/" if kind == "article" else "/editorial/category/"
    slug = path.removeprefix(prefix)
    if (
        not path.startswith(prefix)
        or not slug
        or "/" in slug
        or "\\" in slug
        or any(ord(character) < 32 for character in slug)
    ):
        raise ValidationError("آدرس کنونیکال باید به صفحه عمومی از همان نوع محتوا اشاره کند.")
    return slug


def validate_article_canonical_url(value: str) -> None:
    canonical_path(value, kind="article")


def validate_category_canonical_url(value: str) -> None:
    canonical_path(value, kind="category")


def effective_canonical_url(value: str, *, kind: str, own_slug: str) -> str:
    """Return an override only while its destination is still public and self-canonical."""
    if not value:
        return ""
    try:
        target_slug = canonical_path(value, kind=kind)
    except ValidationError:
        return ""
    if target_slug == own_slug:
        return value

    # Local import avoids a cycle: model field validators live in this module.
    from .models import EditorialArticle, EditorialCategory

    visible = {
        "status": EditorialArticle.Status.PUBLISHED,
        "published_at__isnull": False,
        "published_at__lte": timezone.now(),
    }
    if kind == "article":
        return (
            value
            if EditorialArticle.objects.filter(
                slug=target_slug, seo_noindex=False, seo_canonical_url="", **visible
            ).exists()
            else ""
        )
    return (
        value
        if EditorialCategory.objects.filter(
            slug=target_slug,
            is_active=True,
            seo_noindex=False,
            seo_canonical_url="",
            articles__seo_noindex=False,
            articles__seo_canonical_url="",
            **{f"articles__{key}": val for key, val in visible.items()},
        ).exists()
        else ""
    )
