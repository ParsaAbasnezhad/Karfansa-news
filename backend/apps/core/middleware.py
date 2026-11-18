"""Apply a narrow CSP where the response contract has no executable content."""

from collections.abc import Callable

from django.http import HttpRequest, HttpResponse


class SafeResponseCSPMiddleware:
    def __init__(self, get_response: Callable[[HttpRequest], HttpResponse]) -> None:
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        response = self.get_response(request)
        content_type = response.get("Content-Type", "").partition(";")[0].strip().lower()
        if content_type == "application/json":
            response["Content-Security-Policy"] = (
                "default-src 'none'; base-uri 'none'; frame-ancestors 'none'"
            )
        elif response.status_code in {404, 500} and content_type == "text/html":
            response["Content-Security-Policy"] = (
                "default-src 'none'; style-src 'unsafe-inline'; "
                "base-uri 'none'; form-action 'none'; frame-ancestors 'none'"
            )
        return response
