"""Security checks for explicitly trusted ingress metadata and Admin throttling."""

from django.core.cache import cache
from django.http import HttpResponse
from django.test import RequestFactory, override_settings

from apps.common.client_ip import client_ip
from apps.users.middleware import AdminLoginThrottleMiddleware


def test_client_address_does_not_trust_spoofed_header_by_default() -> None:
    request = RequestFactory().get("/", REMOTE_ADDR="203.0.113.10", HTTP_X_REAL_IP="198.51.100.5")

    assert client_ip(request) == "203.0.113.10"


@override_settings(TRUST_X_REAL_IP=True)
def test_trusted_client_address_requires_one_valid_ip() -> None:
    factory = RequestFactory()
    valid = factory.get("/", REMOTE_ADDR="203.0.113.10", HTTP_X_REAL_IP="198.51.100.5")
    forged_list = factory.get(
        "/", REMOTE_ADDR="203.0.113.10", HTTP_X_REAL_IP="198.51.100.5, 10.0.0.1"
    )

    assert client_ip(valid) == "198.51.100.5"
    assert client_ip(forged_list) == "203.0.113.10"


def test_admin_login_is_rate_limited() -> None:
    cache.clear()
    middleware = AdminLoginThrottleMiddleware(lambda request: HttpResponse("ok"))
    factory = RequestFactory()

    responses = [
        middleware(factory.post("/admin/login/", {"username": "editor"})) for _ in range(11)
    ]

    assert all(response.status_code == 200 for response in responses[:10])
    assert responses[-1].status_code == 429
