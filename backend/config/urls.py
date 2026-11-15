from django.contrib import admin
from django.urls import path

from apps.core.api import api

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/v1/", api.urls),
]

handler404 = "apps.core.views.not_found"
