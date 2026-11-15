from django.http import HttpRequest, HttpResponse, JsonResponse
from django.views.defaults import page_not_found


def not_found(request: HttpRequest, exception: Exception) -> HttpResponse:
    """JSON 404 for unmatched API paths, default Django 404 page elsewhere."""
    if request.path.startswith("/api/"):
        return JsonResponse(
            {"error": {"code": "not_found", "message": "The requested resource was not found."}},
            status=404,
        )
    return page_not_found(request, exception)
