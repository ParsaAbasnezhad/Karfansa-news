"""Read queries for editorial news."""

from django.db.models import Case, IntegerField, Max, Q, QuerySet, Value, When
from django.db.models.functions import Coalesce

from apps.news.models import News, NewsSource, NewsTopic

PUBLIC_ORDERING = frozenset({"-published_at", "published_at"})


def list_rss_news(
    *,
    topic: str = "",
    query: str = "",
    ordering: str = "-published_at",
) -> QuerySet[News]:
    """Return scorer-approved RSS news for the public news listing.

    Only approved, published items in active topics are publicly visible.
    """
    news = (
        News.objects.filter(
            topic__isnull=False,
            topic__is_active=True,
            score__gt=0,
            is_published=True,
            is_archived=False,
        )
        .select_related("source", "topic")
        .annotate(_sort_date=Coalesce("published_at", "fetched_at"))
    )
    if topic:
        news = news.filter(topic__name=topic)
    if query:
        news = news.filter(Q(title__icontains=query) | Q(summary__icontains=query))
    if ordering == "published_at":
        return news.order_by("_sort_date", "id")
    return news.order_by("-_sort_date", "-id")


def list_active_topics() -> QuerySet[NewsTopic]:
    return NewsTopic.objects.filter(is_active=True).order_by("position", "name")


def list_headline_news() -> QuerySet[News]:
    return (
        list_rss_news()
        .annotate(
            _pin_rank=Case(
                When(is_pinned=True, then=Value(0)),
                default=Value(1),
                output_field=IntegerField(),
            ),
            _source_rank=Case(
                When(source__is_headline_source=True, then=Value(0)),
                default=Value(1),
                output_field=IntegerField(),
            ),
        )
        .order_by("_pin_rank", "-score", "_source_rank", "-_sort_date", "-id")
    )


def list_highlight_news(*, exclude_id: int | None = None, limit: int = 3) -> QuerySet[News]:
    news = list_headline_news()
    if exclude_id is not None:
        news = news.exclude(pk=exclude_id)
    return news[:limit]


def latest_refresh_at():
    """Latest successful source fetch, or the newest stored public item."""
    stamp = NewsSource.objects.filter(is_active=True).aggregate(
        value=Max("last_fetched_at"),
    )["value"]
    if stamp is not None:
        return stamp
    return list_rss_news().aggregate(value=Max("fetched_at"))["value"]


def list_pinned_news(*, limit: int = 4) -> QuerySet[News]:
    return list_rss_news().filter(is_pinned=True)[:limit]


def list_topic_sections(*, per_topic: int = 3, topic_limit: int = 6) -> list[dict[str, object]]:
    """Group the newest public items under active topics that actually have news."""
    sections: list[dict[str, object]] = []
    for topic in list_active_topics():
        items = list(list_rss_news(topic=topic.name)[:per_topic])
        if not items:
            continue
        sections.append({"topic": topic.name, "items": items})
        if len(sections) >= topic_limit:
            break
    return sections


def count_active_sources() -> int:
    return NewsSource.objects.filter(is_active=True).count()


def get_public_news(news_id: int) -> News | None:
    return list_rss_news().filter(pk=news_id).first()


def list_related_news(item: News, *, limit: int = 4) -> list[News]:
    topic = item.topic
    if topic is None:
        return []
    return list(list_rss_news(topic=topic.name).exclude(pk=item.pk)[:limit])
