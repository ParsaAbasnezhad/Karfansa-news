"""Exercise secure-cookie and HTTPS behavior used by the production settings."""

import pytest
from django.contrib.auth import get_user_model
from django.test import Client, override_settings


@pytest.mark.django_db
@override_settings(
    DEBUG=False,
    SESSION_COOKIE_SECURE=True,
    CSRF_COOKIE_SECURE=True,
    SESSION_COOKIE_HTTPONLY=True,
)
def test_secure_session_and_csrf_login_flow() -> None:
    user = get_user_model().objects.create_user(
        username="secure-reader",
        email="secure-reader@example.com",
        password="Strong-Password-2026!",
    )
    browser = Client(enforce_csrf_checks=True)
    csrf_response = browser.get("/api/v1/auth/csrf/", secure=True)
    csrf_cookie = csrf_response.cookies["csrftoken"]

    assert csrf_cookie["secure"]
    assert not csrf_cookie["httponly"]  # The browser client reads it for X-CSRFToken.
    assert (
        browser.post(
            "/api/v1/auth/login/",
            data={"identifier": user.email, "password": "Strong-Password-2026!"},
            content_type="application/json",
            HTTP_ORIGIN="https://testserver",
            secure=True,
        ).status_code
        == 403
    )

    response = browser.post(
        "/api/v1/auth/login/",
        data={"identifier": user.email, "password": "Strong-Password-2026!"},
        content_type="application/json",
        HTTP_X_CSRFTOKEN=csrf_cookie.value,
        HTTP_ORIGIN="https://testserver",
        secure=True,
    )

    assert response.status_code == 200
    assert response.cookies["sessionid"]["secure"]
    assert response.cookies["sessionid"]["httponly"]
    assert browser.get("/api/v1/auth/me/", secure=True).status_code == 200


@override_settings(SECURE_SSL_REDIRECT=True, SECURE_PROXY_SSL_HEADER=None)
def test_spoofed_forwarded_proto_does_not_bypass_https_redirect() -> None:
    response = Client().get("/api/v1/auth/csrf/", HTTP_X_FORWARDED_PROTO="https")

    assert response.status_code == 301
    assert response["Location"].startswith("https://")


@override_settings(
    SECURE_SSL_REDIRECT=True,
    SECURE_PROXY_SSL_HEADER=("HTTP_X_FORWARDED_PROTO", "https"),
)
def test_trusted_proxy_header_permits_https_request() -> None:
    response = Client().get("/api/v1/auth/csrf/", HTTP_X_FORWARDED_PROTO="https")

    assert response.status_code == 200
