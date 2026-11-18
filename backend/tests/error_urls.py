"""Test-only routes for exercising Django's production 500 handler end to end."""

from django.urls import path


def raise_error(request):
    raise RuntimeError("private-test-marker")


urlpatterns = [
    path("trigger-server-error/", raise_error),
    path("api/trigger-server-error/", raise_error),
]
handler500 = "apps.core.views.server_error"
