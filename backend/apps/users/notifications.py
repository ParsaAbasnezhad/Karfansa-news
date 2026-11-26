# ruff: noqa: RUF001
"""Delivery adapters for account security messages.

OTP delivery is synchronous so a plaintext code is never persisted in the
Celery broker. Only the one-way verifier belongs in durable storage.
"""

from __future__ import annotations

import logging
import re
from email.utils import parseaddr
from typing import Protocol, cast

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.core.mail import EmailMultiAlternatives
from django.utils.module_loading import import_string

logger = logging.getLogger(__name__)

_OTP_RE = re.compile(r"^[0-9]{6}$")
OTP_TTL_SECONDS = 300
_NON_DELIVERY_BACKENDS = {
    "django.core.mail.backends.console.EmailBackend",
    "django.core.mail.backends.dummy.EmailBackend",
    "django.core.mail.backends.filebased.EmailBackend",
    "django.core.mail.backends.locmem.EmailBackend",
}
_PURPOSE_LABELS = {
    "registration": "تأیید ثبت‌نام",
    "login": "ورود به حساب",
    "password_reset": "بازیابی رمز عبور",
    "password_change": "تغییر رمز عبور",
    "email_verification": "تأیید ایمیل",
    "mobile_verification": "تأیید شماره موبایل",
    # The auth layer may use shorter names for these equivalent actions.
    "reset": "بازیابی رمز عبور",
    "change_password": "تغییر رمز عبور",
    "verify_email": "تأیید ایمیل",
    "verify_mobile": "تأیید شماره موبایل",
}


class DeliveryError(Exception):
    """A provider did not confirm acceptance of a security message."""


class SmsProvider(Protocol):
    """Provider adapter contract; implementations own their credentials and API."""

    def send_sms(self, *, destination: str, message: str) -> bool:
        """Return True only when the provider confirmed acceptance."""
        ...


class VerificationSmsProvider(SmsProvider, Protocol):
    """Optional OTP-specific path used by template providers such as Kavenegar."""

    def send_verification_code(self, *, destination: str, code: str, purpose: str) -> bool:
        """Return True only when the provider confirmed OTP acceptance."""
        ...


def validate_sms_backend_settings(*, debug: bool, backend: str) -> None:
    if backend not in {"console", "provider"}:
        raise ImproperlyConfigured("SMS_BACKEND must be either 'console' or 'provider'.")
    if backend == "console" and not debug:
        raise ImproperlyConfigured("SMS_BACKEND=console is only allowed when DEBUG=True.")


def _mask_sms_destination(destination: str) -> str:
    digits = re.sub(r"\D", "", destination)
    if digits.startswith("98") and len(digits) == 12:
        digits = "0" + digits[2:]
    if len(digits) < 8:
        return "***"
    return f"{digits[:4]}***{digits[-4:]}"


class ConsoleSmsBackend:
    """Log development SMS locally without making any network requests."""

    def send_verification_code(self, *, destination: str, code: str, purpose: str) -> bool:
        logger.info(
            "\n========================================\n"
            "[DEVELOPMENT SMS]\n"
            "Purpose: %s\n"
            "Destination: %s\n"
            "OTP Code: %s\n"
            "Expires in: %s seconds\n"
            "========================================",
            purpose,
            _mask_sms_destination(destination),
            code,
            OTP_TTL_SECONDS,
        )
        return True

    def send_sms(self, *, destination: str, message: str) -> bool:
        logger.info(
            "\n========================================\n"
            "[DEVELOPMENT SMS]\n"
            "Destination: %s\n"
            "Message: %s\n"
            "========================================",
            _mask_sms_destination(destination),
            message,
        )
        return True


class DevelopmentSmsPreviewProvider:
    """Deliver SMS previews to a configured developer mailbox, only in DEBUG.

    This is deliberately a preview, not a production SMS gateway. It lets a
    local developer complete the flow without inventing an undocumented API.
    """

    def send_sms(self, *, destination: str, message: str) -> bool:
        inbox = getattr(settings, "SMS_DEV_INBOX", "")
        if not settings.DEBUG or not inbox:
            raise DeliveryError("SMS delivery is unavailable")
        email = EmailMultiAlternatives(
            subject="Karfansa development SMS preview",
            body=f"Development SMS preview for {destination}:\n\n{message}",
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[inbox],
        )
        return email.send(fail_silently=False) == 1


def _sms_provider() -> SmsProvider:
    backend = getattr(settings, "SMS_BACKEND", "provider")
    validate_sms_backend_settings(debug=settings.DEBUG, backend=backend)
    if backend == "console":
        return ConsoleSmsBackend()

    provider_path = getattr(settings, "SMS_PROVIDER_CLASS", "")
    if provider_path:
        try:
            provider_class = import_string(provider_path)
            return cast("SmsProvider", provider_class())
        except (ImportError, AttributeError, TypeError, ValueError):
            logger.error("auth_sms_provider_configuration_invalid")
            raise DeliveryError("SMS delivery is unavailable") from None
    dev_inbox = getattr(settings, "SMS_DEV_INBOX", "")
    if settings.DEBUG and dev_inbox:
        return DevelopmentSmsPreviewProvider()
    raise DeliveryError("SMS delivery is unavailable")


def _require_real_email_backend() -> None:
    if settings.DEBUG:
        return
    backend = settings.EMAIL_BACKEND
    _, sender_address = parseaddr(settings.DEFAULT_FROM_EMAIL)
    sender_domain = sender_address.rpartition("@")[2].lower()
    if backend in _NON_DELIVERY_BACKENDS or sender_domain in {"", "localhost", "invalid"}:
        raise DeliveryError("Production email delivery is not configured")


def _send_email(destination: str, code: str, label: str) -> bool:
    _require_real_email_backend()
    subject = f"کد {label} کرفنسا"
    body = (
        f"درود،\n\nکد {label} شما: {code}\n"
        "این کد تا ۵ دقیقه معتبر است. اگر این درخواست را ثبت نکرده‌اید، "
        "این پیام را نادیده بگیرید.\n\nکرفنسا"
    )
    html = (
        '<div dir="rtl" lang="fa" style="font-family:Tahoma,Arial,sans-serif;'
        'line-height:1.9;color:#17212b;max-width:520px;margin:auto;padding:24px">'
        '<h1 style="font-size:22px;margin:0 0 16px">کرفنسا</h1>'
        "<p>درود،</p>"
        f"<p>کد {label} شما:</p>"
        f'<p style="font-size:30px;font-weight:700;letter-spacing:8px;direction:ltr;'
        f'text-align:center;background:#f1f5f9;padding:14px;border-radius:10px">{code}</p>'
        "<p>این کد تا <strong>۵ دقیقه</strong> معتبر است.</p>"
        "<p>اگر این درخواست را ثبت نکرده‌اید، این پیام را نادیده بگیرید.</p>"
        "</div>"
    )
    email = EmailMultiAlternatives(
        subject=subject,
        body=body,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[destination],
    )
    email.attach_alternative(html, "text/html")
    return email.send(fail_silently=False) == 1


def _send_sms_otp(*, destination: str, code: str, purpose: str, label: str) -> bool:
    provider = _sms_provider()
    send_verification = getattr(provider, "send_verification_code", None)
    if callable(send_verification):
        return bool(
            cast("VerificationSmsProvider", provider).send_verification_code(
                destination=destination, code=code, purpose=purpose
            )
        )
    return provider.send_sms(
        destination=destination,
        message=(
            f"کد {label} کرفنسا: {code}\n"
            "اعتبار: ۵ دقیقه. اگر درخواست نداده‌اید، این پیام را نادیده بگیرید."
        ),
    )


def send_otp(*, destination: str, channel: str, code: str, purpose: str) -> None:
    """Send a six-digit code, or fail closed if delivery is not accepted."""
    if not _OTP_RE.fullmatch(code):
        raise ValueError("OTP must be a six-digit code")
    label = _PURPOSE_LABELS.get(purpose)
    if label is None:
        raise ValueError("Unknown OTP purpose")
    if channel not in {"email", "sms"}:
        raise ValueError("Unknown delivery channel")
    try:
        if channel == "email":
            accepted = _send_email(destination, code, label)
        else:
            accepted = _send_sms_otp(
                destination=destination, code=code, purpose=purpose, label=label
            )
    except Exception:
        logger.warning("auth_otp_delivery_failed", extra={"channel": channel})
        raise DeliveryError("Security code delivery failed") from None
    if accepted is not True:
        logger.warning("auth_otp_delivery_rejected", extra={"channel": channel})
        raise DeliveryError("Security code delivery was not accepted")


def send_password_changed_notice(*, destination: str) -> None:
    """Send a security notice without any password or OTP content."""
    _require_real_email_backend()
    email = EmailMultiAlternatives(
        subject="رمز عبور حساب کرفنسا تغییر کرد",
        body=(
            "درود،\n\nرمز عبور حساب کرفنسا شما تغییر کرد. "
            "اگر این کار را انجام نداده‌اید، فوراً برای بازیابی حساب اقدام کنید.\n\nکرفنسا"
        ),
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[destination],
    )
    try:
        accepted = email.send(fail_silently=False)
    except Exception:
        logger.warning("auth_security_notice_delivery_failed")
        raise DeliveryError("Security notice delivery failed") from None
    if accepted != 1:
        logger.warning("auth_security_notice_delivery_rejected")
        raise DeliveryError("Security notice delivery was not accepted")


def send_password_changed_sms_notice(*, destination: str) -> None:
    """Notify a verified mobile without placing any secret in the message."""
    try:
        accepted = _sms_provider().send_sms(
            destination=destination,
            message=(
                "رمز عبور حساب کرفنسا شما تغییر کرد. "
                "اگر این کار را انجام نداده‌اید، فوراً برای بازیابی حساب اقدام کنید."
            ),
        )
    except Exception:
        logger.warning("auth_security_notice_delivery_failed", extra={"channel": "sms"})
        raise DeliveryError("Security notice delivery failed") from None
    if accepted is not True:
        logger.warning("auth_security_notice_delivery_rejected", extra={"channel": "sms"})
        raise DeliveryError("Security notice delivery was not accepted")


def queue_security_notice(user_id: int) -> None:
    """Queue a non-secret notice; use direct delivery if the broker is down."""
    from apps.users.tasks import deliver_password_changed_notice

    try:
        deliver_password_changed_notice.apply_async(args=(user_id,), retry=False)
    except Exception:
        logger.warning("auth_security_notice_queue_failed")
        # A broker outage should not silently suppress a security notice.
        from apps.users.tasks import deliver_notice_for_user

        try:
            deliver_notice_for_user(user_id)
        except DeliveryError:
            logger.warning("auth_security_notice_fallback_failed")
