"""API schemas for editorial news."""

from datetime import datetime

from ninja import Schema

from apps.news.models import News


class NewsItemOut(Schema):
    id: int
    title: str
    summary: str
    source_name: str
    source_website: str
    topic: str
    original_url: str
    image_url: str
    published_at: datetime | None
    fetched_at: datetime
    score: int
    is_pinned: bool

    @staticmethod
    def resolve_source_name(obj: News) -> str:
        return obj.source.name

    @staticmethod
    def resolve_source_website(obj: News) -> str:
        return obj.source.website_url

    @staticmethod
    def resolve_topic(obj: News) -> str:
        topic = obj.topic
        return topic.name if topic is not None else ""


class TopicSectionOut(Schema):
    topic: str
    items: list[NewsItemOut]


class NewsListOut(Schema):
    results: list[NewsItemOut]
    topics: list[str]
    count: int
    page: int
    page_size: int
    total_pages: int
    updated_at: datetime | None


class HeadlinesOut(Schema):
    featured: NewsItemOut | None
    minis: list[NewsItemOut]
    latest: list[NewsItemOut]
    pinned: list[NewsItemOut]
    highlights: list[NewsItemOut]
    sections: list[TopicSectionOut]
    source_count: int
    updated_at: datetime | None


class NewsDetailOut(Schema):
    item: NewsItemOut
    related: list[NewsItemOut]
