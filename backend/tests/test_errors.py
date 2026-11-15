import json

from django.test import Client


def test_unknown_route_uses_error_envelope(client: Client) -> None:
    response = client.get("/api/v1/does-not-exist")

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "not_found"


def test_openapi_schema_is_served(client: Client) -> None:
    response = client.get("/api/v1/openapi.json")

    assert response.status_code == 200
    assert json.loads(response.content)["info"]["title"] == "Karfansa News API"
