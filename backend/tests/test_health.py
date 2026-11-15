from django.test import Client

from apps.core import health


def test_health_ok(client: Client, monkeypatch) -> None:  # type: ignore[no-untyped-def]
    monkeypatch.setattr(health, "check_database", lambda: health.CHECK_OK)
    monkeypatch.setattr(health, "check_redis", lambda: health.CHECK_OK)

    response = client.get("/api/v1/health/")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "checks": {"database": "ok", "redis": "ok"},
    }


def test_health_degraded_returns_503(client: Client, monkeypatch) -> None:  # type: ignore[no-untyped-def]
    monkeypatch.setattr(health, "check_database", lambda: health.CHECK_OK)
    monkeypatch.setattr(health, "check_redis", lambda: health.CHECK_FAILED)

    response = client.get("/api/v1/health/")

    assert response.status_code == 503
    assert response.json()["status"] == "degraded"
    assert response.json()["checks"]["redis"] == "unavailable"
