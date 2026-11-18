"""Root Django Ninja API (v1) and its centralized exception handling."""

import logging

from django.http import HttpRequest, HttpResponse
from ninja import NinjaAPI, Router, Status
from ninja.errors import ValidationError

from apps.advertising.api import router as advertising_router
from apps.common.exceptions import AppError
from apps.contact.api import router as contact_router
from apps.core import health
from apps.core.schemas import HealthOut
from apps.editorial.api import router as editorial_router
from apps.news.api import router as news_router
from apps.pages.api import router as pages_router
from apps.users.api import router as auth_router

logger = logging.getLogger(__name__)

api = NinjaAPI(
    title="Karfansa News API",
    version="1.0.0",
    urls_namespace="api-v1",
    docs_url="/docs",
)

system_router = Router(tags=["system"])


@system_router.get("/health/", response={200: HealthOut, 503: HealthOut}, summary="Health check")
def health_check(request: HttpRequest) -> Status[HealthOut]:
    checks = {"database": health.check_database(), "redis": health.check_redis()}
    healthy = all(result == health.CHECK_OK for result in checks.values())
    body = HealthOut(status="ok" if healthy else "degraded", checks=checks)
    return Status(200 if healthy else 503, body)


api.add_router("", system_router)
api.add_router("/news", news_router, tags=["news"])
api.add_router("/editorial", editorial_router, tags=["editorial"])
api.add_router("/contact", contact_router, tags=["contact"])
api.add_router("/auth", auth_router, tags=["auth"])
api.add_router("/advertising", advertising_router, tags=["advertising"])
api.add_router("/pages", pages_router, tags=["pages"])


def _error_response(
    request: HttpRequest, status: int, code: str, message: str, details: object | None = None
) -> HttpResponse:
    body: dict[str, object] = {"code": code, "message": message}
    if details is not None:
        body["details"] = details
    return api.create_response(request, {"error": body}, status=status)


@api.exception_handler(AppError)
def handle_app_error(request: HttpRequest, exc: AppError) -> HttpResponse:
    return _error_response(request, exc.status_code, exc.code, exc.message, exc.details)


@api.exception_handler(ValidationError)
def handle_validation_error(request: HttpRequest, exc: ValidationError) -> HttpResponse:
    return _error_response(
        request, 422, "validation_error", "Request validation failed.", exc.errors
    )


@api.exception_handler(Exception)
def handle_unexpected_error(request: HttpRequest, exc: Exception) -> HttpResponse:
    logger.exception("Unhandled exception", extra={"path": request.path})
    return _error_response(request, 500, "internal_error", "An unexpected error occurred.")
