"""Public editorial queries; every endpoint starts with the same visibility rule."""

from django.db.models import Count, Q, QuerySet
from django.utils import timezone

from .models import EditorialArticle, EditorialCategory

PUBLIC_ORDERING = frozenset({"-published_at", "published_at", "priority"})


def public_articles() -> QuerySet[EditorialArticle]:
    return (
        EditorialArticle.objects.filter(
            status=EditorialArticle.Status.PUBLISHED,
            published_at__isnull=False,
            published_at__lte=timezone.now(),
        )
        .select_related("category", "author", "editor")
        .prefetch_related("tags", "gallery")
    )


def featured_articles() -> QuerySet[EditorialArticle]:
    return public_articles().order_by("-is_pinned", "-priority", "-published_at", "-id")


def list_articles(
    *, category: str = "", query: str = "", ordering: str = "-published_at"
) -> QuerySet[EditorialArticle]:
    articles = public_articles()
    if category:
        articles = articles.filter(category__slug=category)
    if query:
        articles = articles.filter(
            Q(title__icontains=query) | Q(summary__icontains=query) | Q(content__icontains=query)
        )
    if ordering == "published_at":
        return articles.order_by("published_at", "id")
    if ordering == "priority":
        return articles.order_by("-is_pinned", "-priority", "-published_at", "-id")
    return articles.order_by("-published_at", "-id")


def list_categories() -> QuerySet[EditorialCategory]:
    return (
        EditorialCategory.objects.filter(is_active=True)
        .annotate(
            public_count=Count(
                "articles",
                filter=Q(
                    articles__status=EditorialArticle.Status.PUBLISHED,
                    articles__published_at__lte=timezone.now(),
                ),
            )
        )
        .filter(public_count__gt=0)
        .order_by("position", "name")
    )
