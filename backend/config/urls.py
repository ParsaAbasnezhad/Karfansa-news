from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path

from apps.core.api import api
from apps.editorial.sitemap import editorial_sitemap

admin.site.site_header = "کارفنسا نیوز"
admin.site.site_title = "مدیریت کارفنسا"
admin.site.index_title = "پنل مدیریت محتوا"

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/v1/", api.urls),
    path("sitemap.xml", editorial_sitemap, name="editorial-sitemap"),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

handler404 = "apps.core.views.not_found"
handler500 = "apps.core.views.server_error"
