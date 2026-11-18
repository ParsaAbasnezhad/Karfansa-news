"""Smoke the actual public URL configuration with an empty test database."""

import pytest
from django.test import Client


@pytest.mark.django_db
@pytest.mark.parametrize(
    "path,expected_key",
    [
        ("/api/v1/editorial/", "results"),
        ("/api/v1/editorial/latest/", "results"),
        ("/api/v1/editorial/featured/", "featured"),
        ("/api/v1/editorial/categories/", "results"),
        ("/api/v1/news/", "results"),
        ("/api/v1/news/headlines/", "featured"),
        ("/api/v1/advertising/slides/", "results"),
        ("/api/v1/pages/about/", "title"),
    ],
)
def test_public_api_contracts(client: Client, path: str, expected_key: str) -> None:
    response = client.get(path)

    assert response.status_code == 200, path
    assert expected_key in response.json(), path


@pytest.mark.django_db
def test_health_and_unauthorized_identity(client: Client, monkeypatch) -> None:
    # Exercise the HTTP contract without depending on a local Redis daemon.
    monkeypatch.setattr("apps.core.health.check_redis", lambda: "ok")
    health = client.get("/api/v1/health/")
    identity = client.get("/api/v1/auth/me/")

    assert health.status_code == 200
    assert health.json()["status"] == "ok"
    assert identity.status_code == 401
    assert identity.json()["error"]["code"] == "authentication_required"
