"""API endpoints for editorial news."""

from math import ceil

from django.http import HttpRequest
from ninja import Query, Router

from apps.common.exceptions import AppError, NotFoundError
from apps.news import selectors
from apps.news.schemas import HeadlinesOut, NewsDetailOut, NewsListOut

router = Router()


@router.get("/headlines/", response=HeadlinesOut, operation_id="news_headlines")
def news_headlines(request: HttpRequest) -> dict[str, object]:
    headlines = selectors.list_headline_news()
    latest = selectors.list_rss_news()
    featured = headlines.first()
    return {
        "featured": featured,
        "minis": (
            headlines.filter(source_id=featured.source_id).exclude(pk=featured.pk)[:2]
            if featured
            else []
        ),
        "latest": latest[:6],
        "pinned": selectors.list_pinned_news(),
        "highlights": selectors.list_highlight_news(
            exclude_id=featured.pk if featured is not None else None,
        ),
        "sections": selectors.list_topic_sections(),
        "source_count": selectors.count_active_sources(),
        "updated_at": selectors.latest_refresh_at(),
    }


@router.get("/", response=NewsListOut, operation_id="news_list")
def list_news(
    request: HttpRequest,
    topic: str = "",
    q: str = "",
    ordering: str = "-published_at",
    page: int = Query(1, ge=1),
    page_size: int = Query(12, ge=1, le=50),
) -> dict[str, object]:
    order = ordering.strip() or "-published_at"
    if order not in selectors.PUBLIC_ORDERING:
        raise AppError("مرتب‌سازی معتبر نیست.", details={"ordering": order})
    news = selectors.list_rss_news(topic=topic.strip(), query=q.strip(), ordering=order)
    count = news.count()
    start = (page - 1) * page_size
    return {
        "results": news[start : start + page_size],
        "topics": list(selectors.list_active_topics().values_list("name", flat=True)),
        "count": count,
        "page": page,
        "page_size": page_size,
        "total_pages": ceil(count / page_size) if count else 0,
        "updated_at": selectors.latest_refresh_at(),
    }


@router.get("/{news_id}/", response=NewsDetailOut, operation_id="news_detail")
def news_detail(request: HttpRequest, news_id: int) -> dict[str, object]:
    item = selectors.get_public_news(news_id)
    if item is None:
        raise NotFoundError("خبر مورد نظر پیدا نشد.")
    return {"item": item, "related": selectors.list_related_news(item)}
