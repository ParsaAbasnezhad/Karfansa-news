"""Security focused tests for the session and OTP flows."""

from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta

import pytest
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.db import connection
from django.test import Client, RequestFactory
from django.utils import timezone

from apps.users.models import OTPChallenge, ResetAuthorization
from apps.users.notifications import DeliveryError
from apps.users.otp import InvalidChallengeError, consume_challenge, issue_challenge

pytestmark = pytest.mark.django_db


@pytest.fixture(autouse=True)
def auth_env(settings, monkeypatch):
    settings.CACHES = {"default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"}}
    settings.AUTH_PUBLIC_RESPONSE_FLOOR_SECONDS = 0
    cache.clear()
    sent = []

    def capture_otp(*, destination, channel, code, purpose):
        sent.append(
            {"destination": destination, "channel": channel, "code": code, "purpose": purpose}
        )

    monkeypatch.setattr("apps.users.otp.send_otp", capture_otp)
    monkeypatch.setattr("apps.users.services.queue_security_notice", lambda user_id: None)

    def eager_enqueue(challenge_id):
        from apps.users.otp import generate_and_dispatch_challenge

        generate_and_dispatch_challenge(str(challenge_id))
        return True

    monkeypatch.setattr("apps.users.tasks.enqueue_otp_challenge", eager_enqueue)
    return sent


def post(client, path, data):
    return client.post(f"/api/v1/auth/{path}/", data=data, content_type="application/json")


def registered_user(email="reader@example.com", mobile=None):
    user = get_user_model().objects.create_user(
        username="reader",
        email=email,
        normalized_email=email,
        mobile=mobile,
        claimed_mobile=mobile,
        is_contact_signup=True,
        password="Strong-Password-2026!",
        is_active=True,
        email_verified_at=timezone.now() if email else None,
        mobile_verified_at=timezone.now() if mobile else None,
    )
    return user


def registration_payload(**updates):
    data = {
        "first_name": "Ali",
        "last_name": "Ahmadi",
        "email": "ALI@Example.COM",
        "mobile": "۰۹۱۲۱۲۳۴۵۶۷",
        "password": "Strong-Password-2026!",
        "password_confirmation": "Strong-Password-2026!",
        "verification_method": "email",
    }
    data.update(updates)
    return data


def test_registration_activation_and_secondary_contact_verification(client, auth_env):
    response = post(client, "register", registration_payload())
    assert response.status_code == 201
    user = get_user_model().objects.get(email="ali@example.com")
    assert not user.is_active
    assert user.password.startswith("argon2$")
    assert user.mobile == "+989121234567"
    assert user.claimed_mobile is None
    challenge_id = response.json()["challenge_id"]
    assert OTPChallenge.objects.get(pk=challenge_id).verifier != auth_env[-1]["code"]

    verified = post(
        client, "verify-registration", {"challenge_id": challenge_id, "code": auth_env[-1]["code"]}
    )
    assert verified.status_code == 200
    assert verified.json()["user"]["email_verified"] is True
    assert verified.json()["user"]["mobile_verified"] is False
    assert client.get("/api/v1/auth/me/").status_code == 200
    assert (
        post(
            client, "login", {"identifier": "09121234567", "password": "Strong-Password-2026!"}
        ).status_code
        == 401
    )

    request = post(client, "request-contact-verification", {"method": "sms"})
    assert request.status_code == 200
    result = post(
        client,
        "verify-contact",
        {"challenge_id": request.json()["challenge_id"], "code": auth_env[-1]["code"]},
    )
    assert result.status_code == 200
    assert result.json()["user"]["mobile_verified"] is True
    assert (
        post(
            client, "login", {"identifier": "09121234567", "password": "Strong-Password-2026!"}
        ).status_code
        == 200
    )


def test_duplicate_and_invalid_registration(client, auth_env):
    registered_user(email="ali@example.com", mobile="+989121234567")
    duplicate = post(client, "register", registration_payload())
    assert duplicate.status_code == 201
    assert "challenge_id" in duplicate.json()
    assert get_user_model().objects.count() == 1
    assert auth_env == []
    assert post(client, "register", registration_payload(email="invalid")).status_code == 422
    assert post(client, "register", registration_payload(mobile="12345")).status_code == 422


def test_password_login_legacy_compatibility_and_csrf(auth_env):
    user = get_user_model().objects.create_user(
        username="legacy", email="legacy@example.com", password="Strong-Password-2026!"
    )
    browser = Client(enforce_csrf_checks=True)
    assert browser.get("/api/v1/auth/me/").status_code == 401
    no_csrf = post(
        browser, "login", {"identifier": user.email, "password": "Strong-Password-2026!"}
    )
    assert no_csrf.status_code == 403
    browser.get("/api/v1/auth/csrf/")
    token = browser.cookies["csrftoken"].value
    with_csrf = browser.post(
        "/api/v1/auth/login/",
        data={"identifier": user.email, "password": "Strong-Password-2026!"},
        content_type="application/json",
        HTTP_X_CSRFTOKEN=token,
    )
    assert with_csrf.status_code == 200
    assert browser.get("/api/v1/auth/me/").json()["user"]["id"] == user.pk
    assert (
        post(Client(), "login", {"identifier": user.email, "password": "wrong"}).status_code == 401
    )
    assert (
        post(
            Client(), "login", {"identifier": "legacy", "password": "Strong-Password-2026!"}
        ).status_code
        == 200
    )


def test_profile_read_and_update_only_affects_current_user(client):
    user = registered_user()
    other = get_user_model().objects.create_user(username="other", password="safe-password")
    post(client, "login", {"identifier": user.email, "password": "Strong-Password-2026!"})

    current = client.get("/api/v1/auth/me/")
    assert current.status_code == 200
    assert current.json()["user"]["date_joined"]

    updated = client.patch(
        "/api/v1/auth/me/",
        data={"first_name": "سارا", "last_name": "احمدی"},
        content_type="application/json",
    )
    assert updated.status_code == 200
    assert updated.json()["user"]["first_name"] == "سارا"
    user.refresh_from_db()
    other.refresh_from_db()
    assert (user.first_name, user.last_name) == ("سارا", "احمدی")
    assert other.first_name == ""

    invalid = client.patch(
        "/api/v1/auth/me/",
        data={"first_name": " ", "last_name": "احمدی"},
        content_type="application/json",
    )
    assert invalid.status_code == 422
    assert Client().patch(
        "/api/v1/auth/me/",
        data={"first_name": "سارا", "last_name": "احمدی"},
        content_type="application/json",
    ).status_code == 401


def test_otp_expiration_attempts_reuse_and_resend(client, auth_env):
    user = registered_user()
    request = post(client, "request-login-otp", {"identifier": user.email})
    cid = request.json()["challenge_id"]
    code = auth_env[-1]["code"]
    cooldown = post(client, "resend-otp", {"challenge_id": cid})
    assert cooldown.status_code == 200
    assert cooldown.json()["challenge_id"] == cid
    for _ in range(5):
        assert (
            post(
                client,
                "verify-login-otp",
                {"challenge_id": cid, "code": "000001" if code != "000001" else "000002"},
            ).status_code
            == 400
        )
    challenge = OTPChallenge.objects.get(pk=cid)
    assert challenge.attempts == 5
    assert challenge.invalidated_at is not None

    OTPChallenge.objects.filter(pk=cid).update(last_sent_at=timezone.now() - timedelta(seconds=61))
    # A consumed/invalidated challenge cannot be resent.
    assert post(client, "resend-otp", {"challenge_id": cid}).status_code == 200
    request = post(client, "request-login-otp", {"identifier": user.email})
    cid = request.json()["challenge_id"]
    OTPChallenge.objects.filter(pk=cid).update(expires_at=timezone.now() - timedelta(seconds=1))
    assert (
        post(
            client, "verify-login-otp", {"challenge_id": cid, "code": auth_env[-1]["code"]}
        ).status_code
        == 400
    )

    OTPChallenge.objects.filter(pk=cid).update(
        invalidated_at=timezone.now(), last_sent_at=timezone.now() - timedelta(seconds=61)
    )
    fresh = post(client, "request-login-otp", {"identifier": user.email})
    cid = fresh.json()["challenge_id"]
    code = auth_env[-1]["code"]
    assert post(client, "verify-login-otp", {"challenge_id": cid, "code": code}).status_code == 200
    assert post(client, "verify-login-otp", {"challenge_id": cid, "code": code}).status_code == 400


def test_password_recovery_is_single_use_and_invalidates_sessions(client, auth_env):
    user = registered_user()
    other = Client()
    for browser in (client, other):
        assert (
            post(
                browser, "login", {"identifier": user.email, "password": "Strong-Password-2026!"}
            ).status_code
            == 200
        )
    unknown = post(Client(), "forgot-password", {"identifier": "absent@example.com"})
    known = post(Client(), "forgot-password", {"identifier": user.email})
    assert unknown.status_code == known.status_code == 200
    token_response = post(
        Client(),
        "verify-reset-otp",
        {"challenge_id": known.json()["challenge_id"], "code": auth_env[-1]["code"]},
    )
    assert token_response.status_code == 200
    token = token_response.json()["reset_token"]
    changed = post(
        Client(),
        "reset-password",
        {
            "reset_token": token,
            "new_password": "Even-Stronger-Password-2026!",
            "password_confirmation": "Even-Stronger-Password-2026!",
        },
    )
    assert changed.status_code == 200
    assert ResetAuthorization.objects.get(token_digest__isnull=False).consumed_at is not None
    assert (
        post(
            Client(),
            "reset-password",
            {
                "reset_token": token,
                "new_password": "Another-Strong-Password-2026!",
                "password_confirmation": "Another-Strong-Password-2026!",
            },
        ).status_code
        == 400
    )
    assert client.get("/api/v1/auth/me/").status_code == 401
    assert other.get("/api/v1/auth/me/").status_code == 401
    assert (
        post(
            Client(),
            "login",
            {"identifier": user.email, "password": "Even-Stronger-Password-2026!"},
        ).status_code
        == 200
    )


def test_change_password_requires_verified_otp_and_keeps_only_current_session(client, auth_env):
    user = registered_user()
    second = Client()
    for browser in (client, second):
        post(browser, "login", {"identifier": user.email, "password": "Strong-Password-2026!"})
    payload = {
        "challenge_id": "not-a-uuid",
        "code": "123456",
        "new_password": "Even-Stronger-Password-2026!",
        "password_confirmation": "Even-Stronger-Password-2026!",
    }
    assert post(Client(), "change-password", payload).status_code == 401
    assert post(client, "change-password", payload).status_code == 400
    request = post(client, "request-change-password-otp", {})
    payload["challenge_id"] = request.json()["challenge_id"]
    payload["code"] = auth_env[-1]["code"]
    assert post(client, "change-password", payload).status_code == 200
    assert client.get("/api/v1/auth/me/").status_code == 200
    assert second.get("/api/v1/auth/me/").status_code == 401
    assert post(client, "change-password", payload).status_code == 400


def test_delivery_failure_invalidates_pending_challenge(client, monkeypatch):
    def fail(**kwargs):
        raise DeliveryError("provider rejected")

    monkeypatch.setattr("apps.users.otp.send_otp", fail)
    response = post(client, "register", registration_payload(email="new@example.com", mobile=None))
    assert response.status_code == 201
    user = get_user_model().objects.get(email="new@example.com")
    assert not user.is_active
    challenge = OTPChallenge.objects.get(pk=response.json()["challenge_id"])
    assert challenge.invalidated_at is not None
    assert challenge.delivered_at is None


def test_recovery_rate_limit_and_unknown_account_message(client):
    responses = [
        post(client, "forgot-password", {"identifier": "absent@example.com"}) for _ in range(11)
    ]
    assert all(response.status_code == 200 for response in responses[:10])
    assert responses[-1].status_code == 429


def test_recovery_resend_cooldown_has_same_public_status(client, auth_env):
    user = registered_user()
    known = post(client, "forgot-password", {"identifier": user.email})
    unknown = post(client, "forgot-password", {"identifier": "absent@example.com"})
    known_resend = post(client, "resend-otp", {"challenge_id": known.json()["challenge_id"]})
    unknown_resend = post(client, "resend-otp", {"challenge_id": unknown.json()["challenge_id"]})
    assert known_resend.status_code == unknown_resend.status_code == 200
    assert known_resend.json()["message"] == unknown_resend.json()["message"]


@pytest.mark.django_db(transaction=True)
def test_concurrent_otp_consumption_is_single_use(auth_env):
    if connection.vendor != "postgresql":
        pytest.skip("row locking concurrency is verified on PostgreSQL")
    user = registered_user()
    request = RequestFactory().post("/api/v1/auth/verify-login-otp/")
    challenge = issue_challenge(
        request,
        user,
        OTPChallenge.Purpose.LOGIN,
        OTPChallenge.Channel.EMAIL,
        identifier=user.email,
    )
    code = auth_env[-1]["code"]

    def consume():
        try:
            consume_challenge(request, str(challenge.pk), code, OTPChallenge.Purpose.LOGIN)
            return True
        except InvalidChallengeError:
            return False

    with ThreadPoolExecutor(max_workers=2) as pool:
        assert sorted(pool.map(lambda _: consume(), range(2))) == [False, True]
