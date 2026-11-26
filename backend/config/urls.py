from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path

from apps.core.api import api
from apps.core.public_seo import public_page
from apps.editorial.sitemap import (
    editorial_sitemap,
    editorial_sitemap_page,
    news_sitemap,
    news_sitemap_page,
    robots_txt,
    static_sitemap_page,
)

admin.site.site_header = "کارفنسا نیوز"
admin.site.site_title = "مدیریت کارفنسا"
admin.site.index_title = "پنل مدیریت محتوا"

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/v1/", api.urls),
    path("sitemap.xml", editorial_sitemap, name="editorial-sitemap"),
    path("news-sitemap.xml", news_sitemap, name="news-sitemap"),
    path("robots.txt", robots_txt, name="robots-txt"),
    path("sitemaps/static-<int:page>.xml", static_sitemap_page, name="static-sitemap-page"),
    path(
        "sitemaps/editorial-<int:page>.xml",
        editorial_sitemap_page,
        name="editorial-sitemap-page",
    ),
    path("sitemaps/news-<int:page>.xml", news_sitemap_page, name="news-sitemap-page"),
    path("", public_page, name="public-home"),
    path("news", public_page, name="public-news"),
    path("news/", public_page, name="public-news-slash"),
    path("news/<int:news_id>", public_page, name="public-news-detail"),
    path("news/<int:news_id>/", public_page, name="public-news-detail-slash"),
    path("editorial", public_page, name="public-editorial"),
    path("editorial/", public_page, name="public-editorial-slash"),
    path("editorial/category/<str:slug>", public_page, name="public-editorial-category"),
    path("editorial/category/<str:slug>/", public_page, name="public-editorial-category-slash"),
    path("editorial/<path:slug>", public_page, name="public-editorial-detail"),
    path("authors/<int:author_id>", public_page, name="public-author"),
    path("authors/<int:author_id>/", public_page, name="public-author-slash"),
    path("about", public_page, name="public-about"),
    path("about/", public_page, name="public-about-slash"),
    path("contact", public_page, name="public-contact"),
    path("contact/", public_page, name="public-contact-slash"),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

handler404 = "apps.core.views.not_found"
handler500 = "apps.core.views.server_error"
