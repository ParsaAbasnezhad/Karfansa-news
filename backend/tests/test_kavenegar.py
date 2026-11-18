"""Kavenegar VerifyLookup adapter accepts only confirmed provider responses."""

from types import SimpleNamespace

import pytest
from django.test import override_settings

from apps.users.notifications import DeliveryError, send_otp
from apps.users.providers.kavenegar import KavenegarSmsProvider, _receptor


def test_receptor_normalizes_iranian_e164() -> None:
    assert _receptor("+989121234567") == "09121234567"
    assert _receptor("00989121234567") == "09121234567"
    assert _receptor("09121234567") == "09121234567"


@override_settings(
    KAVENEGAR_API_KEY="test-api-key",
    KAVENEGAR_VERIFY_TEMPLATE="karfansaotp",
    KAVENEGAR_SENDER="",
)
def test_verify_lookup_posts_token_and_template(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[dict[str, object]] = []

    class FakeResponse:
        status_code = 200

        @staticmethod
        def json() -> dict[str, object]:
            return {"return": {"status": 200, "message": "تایید شد"}, "entries": []}

    def fake_post(url: str, data: str, headers: dict[str, str], timeout: int) -> FakeResponse:
        calls.append({"url": url, "data": data, "headers": headers, "timeout": timeout})
        return FakeResponse()

    monkeypatch.setattr("apps.users.providers.kavenegar.requests.post", fake_post)
    provider = KavenegarSmsProvider()
    assert provider.send_verification_code(
        destination="+989121234567", code="123456", purpose="login"
    )
    assert len(calls) == 1
    assert calls[0]["url"] == "https://api.kavenegar.com/v1/test-api-key/verify/lookup.json"
    assert "receptor=09121234567" in str(calls[0]["data"])
    assert "token=123456" in str(calls[0]["data"])
    assert "template=karfansaotp" in str(calls[0]["data"])
    assert "type=sms" in str(calls[0]["data"])
    assert "123456" not in str(calls[0]["url"])


@override_settings(
    KAVENEGAR_API_KEY="test-api-key",
    KAVENEGAR_VERIFY_TEMPLATE="karfansaotp",
    SMS_PROVIDER_CLASS="apps.users.providers.kavenegar.KavenegarSmsProvider",
)
def test_send_otp_uses_verify_lookup_path(monkeypatch: pytest.MonkeyPatch) -> None:
    seen: list[dict[str, str]] = []

    def accept(**kwargs: str) -> bool:
        seen.append(kwargs)
        return True

    provider = SimpleNamespace(
        send_verification_code=accept,
        send_sms=lambda **_: False,
    )
    monkeypatch.setattr(
        "apps.users.notifications.import_string",
        lambda _path: lambda: provider,
    )
    send_otp(destination="+989121234567", channel="sms", code="654321", purpose="login")
    assert seen == [{"destination": "+989121234567", "code": "654321", "purpose": "login"}]


@override_settings(KAVENEGAR_API_KEY="", KAVENEGAR_VERIFY_TEMPLATE="karfansaotp")
def test_missing_api_key_fails_closed() -> None:
    with pytest.raises(ValueError):
        KavenegarSmsProvider()


@override_settings(
    KAVENEGAR_API_KEY="test-api-key",
    KAVENEGAR_VERIFY_TEMPLATE="karfansaotp",
)
def test_provider_rejection_is_not_acceptance(monkeypatch: pytest.MonkeyPatch) -> None:
    class FakeResponse:
        status_code = 200

        @staticmethod
        def json() -> dict[str, object]:
            return {"return": {"status": 424, "message": "template missing"}}

    monkeypatch.setattr(
        "apps.users.providers.kavenegar.requests.post",
        lambda *args, **kwargs: FakeResponse(),
    )
    provider = KavenegarSmsProvider()
    assert (
        provider.send_verification_code(destination="+989121234567", code="123456", purpose="login")
        is False
    )


@override_settings(
    DEBUG=False,
    SMS_PROVIDER_CLASS="apps.users.providers.kavenegar.KavenegarSmsProvider",
    KAVENEGAR_API_KEY="test-api-key",
    KAVENEGAR_VERIFY_TEMPLATE="",
)
def test_missing_template_rejects_otp_delivery(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "apps.users.providers.kavenegar.requests.post",
        lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("should not call API")),
    )
    with pytest.raises(DeliveryError):
        send_otp(destination="+989121234567", channel="sms", code="123456", purpose="login")
