"""Public wire contract for editorial endpoints."""

from datetime import datetime

from ninja import Schema


class CategoryOut(Schema):
    id: int
    slug: str
    name: str
    seo_title: str
    seo_description: str
    seo_social_image_url: str
    seo_noindex: bool
    seo_canonical_url: str


class GalleryImageOut(Schema):
    id: int
    image_url: str
    image_srcset: str
    width: int | None
    height: int | None
    alt_text: str
    caption: str


class ArticleOut(Schema):
    id: int
    slug: str
    title: str
    summary: str
    source_url: str
    featured_image_url: str
    featured_image_srcset: str
    featured_image_width: int | None
    featured_image_height: int | None
    category: CategoryOut | None
    tags: list[str]
    author_name: str
    author_id: int | None
    published_at: datetime
    updated_at: datetime
    reading_time: int
    is_featured: bool
    is_breaking: bool
    is_pinned: bool
    priority: int


class ArticleDetailOut(ArticleOut):
    content: str
    gallery: list[GalleryImageOut]
    editor_name: str
    source_name: str
    seo_title: str
    seo_description: str
    seo_social_image_url: str
    seo_noindex: bool
    seo_canonical_url: str
    view_count: int


class ArticleListOut(Schema):
    results: list[ArticleOut]
    categories: list[CategoryOut]
    count: int
    page: int
    page_size: int
    total_pages: int


class FeaturedOut(Schema):
    featured: ArticleOut | None
    secondary: list[ArticleOut]


class LatestOut(Schema):
    results: list[ArticleOut]


class CategoriesOut(Schema):
    results: list[CategoryOut]


class ArticleDetailResponse(Schema):
    item: ArticleDetailOut
    related: list[ArticleOut]
