"""Public contact messages for the newsroom."""

import hashlib

from django.core.cache import cache
from django.http import HttpRequest
from django.views.decorators.csrf import csrf_protect, ensure_csrf_cookie
from ninja import Router, Status
from ninja.decorators import decorate_view

from apps.common.exceptions import AppError, RateLimitedError

from .models import ContactMessage
from .schemas import ContactCsrfOut, ContactMessageIn, ContactMessageOut

router = Router()


@router.get("/csrf/", response=ContactCsrfOut, operation_id="contact_csrf")
@decorate_view(ensure_csrf_cookie)
def contact_csrf(request: HttpRequest) -> ContactCsrfOut:
    return ContactCsrfOut(message="ok")


@router.post("/", response={201: ContactMessageOut}, operation_id="contact_message_create")
@decorate_view(csrf_protect)
def create_contact_message(
    request: HttpRequest,
    payload: ContactMessageIn,
) -> Status[ContactMessageOut]:
    if payload.website.strip():
        raise AppError("درخواست معتبر نیست.")

    remote_addr = request.META.get("REMOTE_ADDR", "unknown")
    throttle_id = hashlib.sha256(remote_addr.encode()).hexdigest()
    throttle_key = f"contact-message:{throttle_id}"
    cache.add(throttle_key, 0, timeout=3600)
    attempts = cache.incr(throttle_key)
    if attempts > 5:
        raise RateLimitedError("تعداد پیام‌ها زیاد است. کمی بعد دوباره تلاش کنید.")  # noqa: RUF001

    ContactMessage.objects.create(
        name=payload.name.strip(),
        phone=payload.phone,
        email=payload.email.strip().lower(),
        subject=payload.subject.strip(),
        message=payload.message.strip(),
    )
    return Status(201, ContactMessageOut(message="پیام شما با موفقیت ثبت شد."))
