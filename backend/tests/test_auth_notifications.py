# ruff: noqa: RUF001
"""Notification delivery must acknowledge acceptance and fail closed."""

import logging
import re
from datetime import timedelta
from types import SimpleNamespace
from uuid import uuid4

import pytest
from django.apps import apps as django_apps
from django.contrib.auth import get_user_model
from django.core import mail
from django.core.exceptions import ImproperlyConfigured
from django.test import override_settings
from django.utils import timezone

from apps.users import notifications
from apps.users import tasks as user_tasks
from apps.users.apps import UsersConfig
from apps.users.models import OTPChallenge
from apps.users.notifications import validate_sms_backend_settings
from apps.users.otp import _destination_digest
from apps.users.tasks import deliver_notice_for_user


@override_settings(DEBUG=True, EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
def test_otp_email_has_persian_rtl_and_expiration() -> None:
    notifications.send_otp(
        destination="reader@example.com",
        channel="email",
        code="123456",
        purpose="registration",
    )

    assert len(mail.outbox) == 1
    assert mail.outbox[0].to == ["reader@example.com"]
    assert "123456" in mail.outbox[0].body
    assert "۵ دقیقه" in mail.outbox[0].body
    assert 'dir="rtl"' in mail.outbox[0].alternatives[0].content


def test_otp_email_rejection_is_failure(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(notifications, "_send_email", lambda *_args: False)
    with pytest.raises(notifications.DeliveryError):
        notifications.send_otp(
            destination="reader@example.com",
            channel="email",
            code="123456",
            purpose="login",
        )


@override_settings(
    DEBUG=False,
    EMAIL_BACKEND="django.core.mail.backends.console.EmailBackend",
    DEFAULT_FROM_EMAIL="Karfansa <no-reply@example.com>",
)
def test_production_console_email_is_rejected() -> None:
    with pytest.raises(notifications.DeliveryError):
        notifications.send_otp(
            destination="reader@example.com",
            channel="email",
            code="123456",
            purpose="registration",
        )


@override_settings(
    DEBUG=False,
    EMAIL_BACKEND="django.core.mail.backends.smtp.EmailBackend",
    DEFAULT_FROM_EMAIL="Karfansa <no-reply@localhost>",
)
def test_production_localhost_sender_is_rejected() -> None:
    with pytest.raises(notifications.DeliveryError):
        notifications.send_otp(
            destination="reader@example.com",
            channel="email",
            code="123456",
            purpose="registration",
        )


@override_settings(DEBUG=False, SMS_PROVIDER_CLASS="", SMS_DEV_INBOX="reader@example.com")
def test_sms_fails_closed_without_provider() -> None:
    with pytest.raises(notifications.DeliveryError):
        notifications.send_otp(
            destination="+989121234567",
            channel="sms",
            code="123456",
            purpose="login",
        )


def test_console_sms_backend_is_rejected_without_debug() -> None:
    with override_settings(DEBUG=False, SMS_BACKEND="console"), pytest.raises(ImproperlyConfigured):
        UsersConfig("apps.users", django_apps).ready()
    validate_sms_backend_settings(debug=True, backend="console")


@pytest.mark.django_db
@override_settings(DEBUG=True, SMS_BACKEND="console", SMS_PROVIDER_CLASS="")
def test_celery_otp_task_logs_code_and_persists_verifier(
    monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    now = timezone.now()
    user = get_user_model().objects.create_user(
        username="console-reader",
        mobile="+989121234567",
        claimed_mobile="+989121234567",
        mobile_verified_at=now,
        is_active=True,
    )
    challenge = OTPChallenge.objects.create(
        user=user,
        purpose=OTPChallenge.Purpose.LOGIN,
        channel=OTPChallenge.Channel.SMS,
        destination_digest=_destination_digest("+989121234567"),
        verifier="",
        expires_at=now + timedelta(minutes=5),
        last_sent_at=now,
    )

    def unexpected_provider(_path: str) -> None:
        raise AssertionError("Console SMS must not load or contact an external provider")

    monkeypatch.setattr(notifications, "import_string", unexpected_provider)
    with caplog.at_level(logging.INFO, logger="apps.users.notifications"):
        user_tasks.dispatch_otp_challenge.run(str(challenge.pk))

    challenge.refresh_from_db()
    assert challenge.delivered_at is not None
    assert challenge.verifier
    assert challenge.verifier != ""
    code_match = re.search(r"OTP Code: ([0-9]{6})", caplog.text)
    assert code_match is not None
    assert "Destination: 0912***4567" in caplog.text


@override_settings(
    DEBUG=True,
    SMS_PROVIDER_CLASS="",
    SMS_DEV_INBOX="developer@example.com",
    EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
)
def test_development_sms_preview_uses_configured_mailbox() -> None:
    notifications.send_otp(
        destination="+989121234567",
        channel="sms",
        code="123456",
        purpose="login",
    )
    assert mail.outbox[0].to == ["developer@example.com"]
    assert "+989121234567" in mail.outbox[0].body


@override_settings(DEBUG=False, SMS_PROVIDER_CLASS="providers.Example")
def test_sms_provider_must_confirm_acceptance(monkeypatch: pytest.MonkeyPatch) -> None:
    provider = SimpleNamespace(send_sms=lambda **_kwargs: False)
    monkeypatch.setattr(notifications, "import_string", lambda _path: lambda: provider)

    with pytest.raises(notifications.DeliveryError):
        notifications.send_otp(
            destination="+989121234567",
            channel="sms",
            code="123456",
            purpose="login",
        )


def test_invalid_otp_is_rejected_before_delivery() -> None:
    with pytest.raises(ValueError):
        notifications.send_otp(
            destination="reader@example.com",
            channel="email",
            code="12a456",
            purpose="login",
        )


@pytest.mark.django_db
@override_settings(DEBUG=False, SMS_PROVIDER_CLASS="providers.Example")
def test_mobile_only_password_change_notice_uses_sms(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    user = get_user_model().objects.create_user(
        username="mobile-reader",
        password="safe-password",
        mobile="+989121234567",
        mobile_verified_at=timezone.now(),
    )
    submissions: list[dict[str, str]] = []

    def accept_sms(**kwargs: str) -> bool:
        submissions.append(kwargs)
        return True

    provider = SimpleNamespace(send_sms=accept_sms)
    monkeypatch.setattr(notifications, "import_string", lambda _path: lambda: provider)

    deliver_notice_for_user(user.pk)

    assert len(submissions) == 1
    assert submissions[0]["destination"] == "+989121234567"
    assert "رمز عبور" in submissions[0]["message"]
    assert "123456" not in submissions[0]["message"]


@override_settings(DEBUG=False, SMS_PROVIDER_CLASS="providers.Example")
def test_password_change_sms_rejection_is_failure(monkeypatch: pytest.MonkeyPatch) -> None:
    provider = SimpleNamespace(send_sms=lambda **_kwargs: False)
    monkeypatch.setattr(notifications, "import_string", lambda _path: lambda: provider)
    with pytest.raises(notifications.DeliveryError):
        notifications.send_password_changed_sms_notice(destination="+989121234567")


def test_security_notice_falls_back_when_broker_unavailable(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[int] = []

    def broker_down(*_args: object, **kwargs: object) -> None:
        assert kwargs["retry"] is False
        raise ConnectionError("broker unavailable")

    monkeypatch.setattr(user_tasks.deliver_password_changed_notice, "apply_async", broker_down)
    monkeypatch.setattr(user_tasks, "deliver_notice_for_user", calls.append)

    notifications.queue_security_notice(42)

    assert calls == [42]


def test_otp_enqueue_sends_only_challenge_id_without_publish_retry(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    challenge_id = uuid4()
    calls: list[dict[str, object]] = []
    monkeypatch.setattr(
        user_tasks.dispatch_otp_challenge,
        "apply_async",
        lambda **kwargs: calls.append(kwargs),
    )

    assert user_tasks.enqueue_otp_challenge(challenge_id)
    assert calls == [{"args": (str(challenge_id),), "retry": False}]


def test_otp_enqueue_fails_without_inline_delivery(monkeypatch: pytest.MonkeyPatch) -> None:
    def broker_down(**_kwargs: object) -> None:
        raise ConnectionError("broker unavailable")

    monkeypatch.setattr(user_tasks.dispatch_otp_challenge, "apply_async", broker_down)

    assert not user_tasks.enqueue_otp_challenge(uuid4())
