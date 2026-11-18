"""Bound failed or repeated Django Admin sign-in attempts in production."""

from collections.abc import Callable

from django.http import HttpRequest, HttpResponse

from apps.common.exceptions import RateLimitedError

from .otp import throttle


class AdminLoginThrottleMiddleware:
    def __init__(self, get_response: Callable[[HttpRequest], HttpResponse]) -> None:
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        if request.method == "POST" and request.path == "/admin/login/":
            try:
                throttle(
                    request,
                    "admin-login",
                    identifier=request.POST.get("username", "").strip().casefold()[:254],
                )
            except RateLimitedError:
                return HttpResponse("Too many sign-in attempts. Try again later.", status=429)
        return self.get_response(request)
