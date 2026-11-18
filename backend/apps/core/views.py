from django.http import HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import render


def not_found(request: HttpRequest, exception: Exception) -> HttpResponse:
    """Keep the API contract and render a safe Persian page for browser routes."""
    if request.path.startswith("/api/"):
        return JsonResponse(
            {"error": {"code": "not_found", "message": "The requested resource was not found."}},
            status=404,
        )
    return render(
        request,
        "core/error.html",
        {
            "code": "۴۰۴",
            "title": "صفحه موردنظر پیدا نشد",
            "message": "ممکن است آدرس تغییر کرده باشد یا این صفحه دیگر در دسترس نباشد.",
            "show_latest": True,
        },
        status=404,
    )


def server_error(request: HttpRequest) -> HttpResponse:
    """A database-independent fallback with no exception details in the response."""
    if request.path.startswith("/api/"):
        return JsonResponse(
            {"error": {"code": "internal_error", "message": "An unexpected error occurred."}},
            status=500,
        )
    return render(
        request,
        "core/error.html",
        {
            "code": "۵۰۰",  # noqa: RUF001 - Persian digits in a Persian error page
            "title": "مشکلی در سرور رخ داده است",
            "message": "پردازش درخواست ممکن نیست. لطفاً کمی بعد دوباره تلاش کنید.",
            "show_retry": True,
        },
        status=500,
    )
