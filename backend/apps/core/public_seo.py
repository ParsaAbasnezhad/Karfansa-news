# ruff: noqa: RUF001 - Persian copy contains intentional Arabic-script characters.
"""Small server-rendered entry points for crawlable public React routes.

The interactive application still owns navigation. These responses give the
initial request its real status, published content, metadata and JSON-LD.
"""

import json
from typing import Any
from urllib.parse import quote, unquote, urlsplit

from django.conf import settings
from django.db.models import Exists, OuterRef, QuerySet
from django.http import Http404, HttpRequest, HttpResponse, HttpResponseGone
from django.shortcuts import redirect, render
from django.utils import timezone
from django.utils.html import strip_tags

from apps.editorial.models import EditorialArticle, EditorialCategory
from apps.editorial.sanitizer import sanitize_article_html
from apps.editorial.selectors import public_articles
from apps.editorial.seo import effective_canonical_url
from apps.news.selectors import get_public_news, list_rss_news
from apps.pages.selectors import ensure_about_page, ensure_contact_page

BRAND = "کارفنسا نیوز"
HOME_TITLE = "کارفنسا نیوز | اخبار اقتصادی، تجارت و بازارهای جهانی"
HOME_DESCRIPTION = (
    "کارفنسا نیوز، رسانه خبری و تحلیلی اقتصاد، تجارت، صادرات، واردات، صنایع و بازارهای جهانی."
)
LOGO_PATH = "/KARFANSA%20%E2%80%94%20Logo.svg"


def site_url(path: str = "/") -> str:
    return f"{getattr(settings, 'SEO_SITE_URL', 'https://karfansa.news.ir')}{path}"


def _image_url(field: Any) -> str:
    return site_url(field.url) if field else ""


def _article_path(item: EditorialArticle) -> str:
    return f"/editorial/{quote(item.slug, safe='')}"


def _author_name(item: EditorialArticle) -> str:
    return item.author.get_full_name().strip() if item.author else ""


def _public_categories() -> QuerySet[EditorialCategory]:
    visible = EditorialArticle.objects.filter(
        category_id=OuterRef("pk"),
        status=EditorialArticle.Status.PUBLISHED,
        published_at__isnull=False,
        published_at__lte=timezone.now(),
    )
    return (
        EditorialCategory.objects.filter(is_active=True)
        .alias(has_public=Exists(visible))
        .filter(has_public=True)
        .order_by("position", "name")
    )


def _base_graph() -> list[dict[str, Any]]:
    socials = [
        url
        for url in getattr(settings, "SEO_VERIFIED_SOCIAL_URLS", [])
        if urlsplit(url).scheme == "https"
        and urlsplit(url).hostname
        and not urlsplit(url).username
        and not urlsplit(url).password
    ]
    organization: dict[str, Any] = {
        "@type": "NewsMediaOrganization",
        "@id": site_url("/#organization"),
        "name": BRAND,
        "alternateName": "Karfansa News",
        "url": site_url(),
        "logo": {"@type": "ImageObject", "url": site_url(LOGO_PATH)},
    }
    if socials:
        organization["sameAs"] = socials
    return [
        organization,
        {
            "@type": "WebSite",
            "@id": site_url("/#website"),
            "name": BRAND,
            "alternateName": "Karfansa News",
            "url": site_url(),
            "inLanguage": "fa-IR",
            "publisher": {"@id": site_url("/#organization")},
        },
    ]


def _breadcrumbs(items: list[tuple[str, str]]) -> dict[str, Any]:
    return {
        "@type": "BreadcrumbList",
        "itemListElement": [
            {"@type": "ListItem", "position": index, "name": name, "item": site_url(path)}
            for index, (name, path) in enumerate(items, start=1)
        ],
    }


def _context(
    *,
    title: str,
    description: str,
    canonical: str,
    page_type: str,
    graph: list[dict[str, Any]],
    image: str = "",
    noindex: bool = False,
    **content: Any,
) -> dict[str, Any]:
    graph_json = json.dumps(
        {"@context": "https://schema.org", "@graph": [*_base_graph(), *graph]},
        ensure_ascii=False,
        separators=(",", ":"),
    ).replace("<", "\\u003c")
    return {
        "title": title,
        "description": strip_tags(description).strip()[:320] or title,
        "canonical": canonical,
        "page_type": page_type,
        "json_ld": graph_json,
        "image": image,
        "noindex": noindex,
        "logo_url": LOGO_PATH,
        "verification": getattr(settings, "SEO_GOOGLE_VERIFICATION", ""),
        "app_script": page_type != "author",
        "categories": list(_public_categories()),
        **content,
    }


def _render(request: HttpRequest, context: dict[str, Any]) -> HttpResponse:
    response = render(request, "core/public_seo.html", context)
    response["Cache-Control"] = "public, max-age=60" if not context["noindex"] else "no-store"
    return response


def _clean_path_redirect(request: HttpRequest) -> HttpResponse | None:
    if request.path != "/" and request.path.endswith("/"):
        target = request.path.rstrip("/")
        if request.META.get("QUERY_STRING"):
            target = f"{target}?{request.META['QUERY_STRING']}"
        return redirect(target, permanent=True)
    return None


def public_page(request: HttpRequest, **kwargs: Any) -> HttpResponse:
    """Dispatch only routes explicitly exposed by config.urls."""
    clean = _clean_path_redirect(request)
    if clean is not None:
        return clean

    path = request.path
    if path == "/":
        editorial = list(
            public_articles().prefetch_related(None).order_by("-published_at", "-id")[:8]
        )
        rss = list(list_rss_news()[:8])
        graph = [
            {
                "@type": "CollectionPage",
                "@id": site_url("/#page"),
                "name": HOME_TITLE,
                "url": site_url(),
                "inLanguage": "fa-IR",
                "isPartOf": {"@id": site_url("/#website")},
            }
        ]
        return _render(
            request,
            _context(
                title=HOME_TITLE,
                description=HOME_DESCRIPTION,
                canonical=site_url(),
                page_type="home",
                graph=graph,
                editorials=editorial,
                rss_items=rss,
            ),
        )

    if path == "/news":
        topic = request.GET.get("topic", "").strip()[:100]
        query = request.GET.get("q", "").strip()[:200]
        ordering = request.GET.get("ordering", "-published_at")
        if ordering not in {"-published_at", "published_at"}:
            ordering = "-published_at"
        try:
            page_number = max(1, min(int(request.GET.get("page", "1")), 1000))
        except ValueError:
            page_number = 1
        start = (page_number - 1) * 20
        rss = list(list_rss_news(topic=topic, query=query, ordering=ordering)[start : start + 20])
        if page_number > 1 and not rss:
            raise Http404
        graph = [
            {
                "@type": "CollectionPage",
                "name": "آخرین اخبار",
                "url": site_url(path),
                "inLanguage": "fa-IR",
                "isPartOf": {"@id": site_url("/#website")},
            }
        ]
        return _render(
            request,
            _context(
                title=f"آخرین اخبار اقتصادی و تجارت | {BRAND}",
                description=(
                    "تازه‌ترین خبرهای اقتصادی و تجاری از منابع خبری با ذکر نام و پیوند منبع اصلی."
                ),
                canonical=site_url(path),
                page_type="news_list",
                graph=graph,
                rss_items=rss,
                noindex=bool(request.GET) or not rss,
            ),
        )

    if path == "/editorial":
        legacy_category = request.GET.get("category", "").strip()
        if legacy_category and len(request.GET) == 1:
            category = _public_categories().filter(slug=legacy_category).first()
            if category:
                return redirect(
                    f"/editorial/category/{quote(category.slug, safe='')}", permanent=True
                )
        return _editorial_list(request, category_slug=legacy_category)

    if path.startswith("/editorial/category/"):
        return _editorial_list(request, category_slug=str(kwargs.get("slug", "")))

    if path.startswith("/editorial/"):
        return _editorial_detail(request, str(kwargs.get("slug", "")))

    if path.startswith("/authors/"):
        return _author_page(request, int(kwargs.get("author_id", 0)))

    if path == "/about":
        about_page = ensure_about_page()
        graph = [
            {
                "@type": "AboutPage",
                "name": about_page.title,
                "url": site_url(path),
                "inLanguage": "fa-IR",
                "isPartOf": {"@id": site_url("/#website")},
            },
            _breadcrumbs([(BRAND, "/"), ("درباره ما", path)]),
        ]
        return _render(
            request,
            _context(
                title=about_page.seo_title or f"درباره ما | {BRAND}",
                description=about_page.seo_description or about_page.intro,
                canonical=site_url(path),
                page_type="about",
                graph=graph,
                about=about_page,
                image=_image_url(about_page.hero_image),
            ),
        )

    if path == "/contact":
        contact_page = ensure_contact_page()
        graph = [
            {
                "@type": "ContactPage",
                "name": contact_page.title,
                "url": site_url(path),
                "inLanguage": "fa-IR",
                "isPartOf": {"@id": site_url("/#website")},
            },
            _breadcrumbs([(BRAND, "/"), ("تماس با ما", path)]),
        ]
        return _render(
            request,
            _context(
                title=contact_page.seo_title or f"تماس با ما | {BRAND}",
                description=contact_page.seo_description or contact_page.description,
                canonical=site_url(path),
                page_type="contact",
                graph=graph,
                contact=contact_page,
            ),
        )

    if path.startswith("/news/"):
        item = get_public_news(int(kwargs.get("news_id", 0)))
        if item is None:
            raise Http404
        return _render(
            request,
            _context(
                title=f"{item.title} | {BRAND}",
                description=item.summary or item.title,
                canonical=site_url(path),
                page_type="rss_detail",
                graph=[],
                noindex=True,
                rss_item=item,
            ),
        )

    raise Http404


def _editorial_list(request: HttpRequest, category_slug: str = "") -> HttpResponse:
    category = None
    path = "/editorial"
    articles = public_articles().prefetch_related(None)
    if category_slug:
        category = _public_categories().filter(slug=category_slug).first()
        if category is None:
            raise Http404
        articles = articles.filter(category_id=category.pk)
        path = f"/editorial/category/{quote(category.slug, safe='')}"
    query = request.GET.get("q", "").strip()[:200]
    if query:
        articles = articles.filter(title__icontains=query)
    try:
        page_number = max(1, min(int(request.GET.get("page", "1")), 1000))
    except ValueError:
        page_number = 1
    start = (page_number - 1) * 20
    items = list(articles.order_by("-published_at", "-id")[start : start + 20])
    if page_number > 1 and not items:
        raise Http404
    name = category.name if category else "تحلیل و گزارش"
    title = (
        (getattr(category, "seo_title", "") or f"{name} | {BRAND}")
        if category
        else f"تحلیل و گزارش | {BRAND}"
    )
    description = (
        (
            getattr(category, "seo_description", "")
            or f"گزارش‌ها و خبرهای تحریریه {BRAND} در دسته {name}."
        )
        if category
        else (f"آخرین گزارش‌ها، تحلیل‌ها و خبرهای اختصاصی تحریریه {BRAND}.")
    )
    graph = [
        {
            "@type": "CollectionPage",
            "name": name,
            "url": site_url(path),
            "inLanguage": "fa-IR",
            "isPartOf": {"@id": site_url("/#website")},
        },
        _breadcrumbs(
            [
                (BRAND, "/"),
                ("تحلیل و گزارش", "/editorial"),
                *([(category.name, path)] if category else []),
            ]
        ),
    ]
    canonical_override = (
        effective_canonical_url(category.seo_canonical_url, kind="category", own_slug=category.slug)
        if category
        else ""
    )
    return _render(
        request,
        _context(
            title=title,
            description=description,
            canonical=canonical_override or site_url(path),
            page_type="editorial_list",
            graph=graph,
            editorials=items,
            selected_category=category,
            noindex=bool(request.GET)
            or not items
            or bool(category and category.seo_noindex)
            or bool(category and category.seo_canonical_url and not canonical_override),
            image=_image_url(category.seo_social_image) if category else "",
        ),
    )


def _editorial_detail(request: HttpRequest, slug: str) -> HttpResponse:
    item = public_articles().prefetch_related(None).filter(slug=slug).first()
    if item is None:
        archived = EditorialArticle.objects.filter(
            slug=slug, status=EditorialArticle.Status.ARCHIVED
        ).exists()
        if archived:
            return HttpResponseGone("این خبر دیگر در دسترس نیست.")
        raise Http404
    path = _article_path(item)
    if request.path not in {path, unquote(path)}:
        return redirect(path, permanent=True)
    published_at = item.published_at
    if published_at is None:
        raise Http404
    canonical_override = effective_canonical_url(
        item.seo_canonical_url, kind="article", own_slug=item.slug
    )
    canonical = canonical_override or site_url(path)
    noindex = item.seo_noindex or bool(item.seo_canonical_url and not canonical_override)
    author_name = _author_name(item)
    image = _image_url(item.seo_social_image or item.featured_image)
    article: dict[str, Any] = {
        "@type": "Article" if item.source_url or item.source_name else "NewsArticle",
        "@id": f"{site_url(path)}#article",
        "headline": item.title,
        "description": item.seo_description or item.summary,
        "mainEntityOfPage": canonical,
        "url": site_url(path),
        "datePublished": published_at.isoformat(),
        "dateModified": item.updated_at.isoformat(),
        "inLanguage": "fa-IR",
        "publisher": {"@id": site_url("/#organization")},
    }
    if item.category:
        article["articleSection"] = item.category.name
    if item.featured_image or item.seo_social_image:
        article["image"] = [_image_url(item.featured_image or item.seo_social_image)]
    if author_name:
        article["author"] = {
            "@type": "Person",
            "name": author_name,
            "url": site_url(f"/authors/{item.author_id}"),
        }
    if item.source_url:
        article["isBasedOn"] = item.source_url
    graph = [
        *([] if noindex else [article]),
        _breadcrumbs([(BRAND, "/"), ("تحلیل و گزارش", "/editorial"), (item.title, path)]),
    ]
    return _render(
        request,
        _context(
            title=item.seo_title or f"{item.title} | {BRAND}",
            description=item.seo_description or item.summary,
            canonical=canonical,
            page_type="article",
            graph=graph,
            image=image,
            noindex=noindex,
            article=item,
            author_name=author_name,
            article_html=sanitize_article_html(item.content),
        ),
    )


def _author_page(request: HttpRequest, author_id: int) -> HttpResponse:
    articles = list(
        public_articles()
        .prefetch_related(None)
        .filter(author_id=author_id)
        .order_by("-published_at", "-id")[:20]
    )
    if not articles:
        raise Http404
    name = _author_name(articles[0])
    if not name:
        raise Http404
    path = f"/authors/{author_id}"
    graph = [
        {"@type": "Person", "name": name, "url": site_url(path)},
        {
            "@type": "CollectionPage",
            "name": f"مطالب {name}",
            "url": site_url(path),
            "inLanguage": "fa-IR",
        },
        _breadcrumbs([(BRAND, "/"), (name, path)]),
    ]
    return _render(
        request,
        _context(
            title=f"مطالب {name} | {BRAND}",
            description=f"خبرها و گزارش‌های منتشرشده از {name} در {BRAND}.",
            canonical=site_url(path),
            page_type="author",
            graph=graph,
            editorials=articles,
            author_page_name=name,
        ),
    )
