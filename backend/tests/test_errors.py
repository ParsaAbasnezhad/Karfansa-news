import json

from django.test import Client
from django.test.utils import override_settings


def test_unknown_route_uses_error_envelope(client: Client) -> None:
    response = client.get("/api/v1/does-not-exist")

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "not_found"
    assert "default-src 'none'" in response["Content-Security-Policy"]


def test_openapi_schema_is_served(client: Client) -> None:
    response = client.get("/api/v1/openapi.json")

    assert response.status_code == 200
    assert json.loads(response.content)["info"]["title"] == "Karfansa News API"


@override_settings(DEBUG=False)
def test_production_404_has_real_status_and_safe_persian_page(client: Client) -> None:
    response = client.get("/this-page-does-not-exist/")

    assert response.status_code == 404
    assert "صفحه موردنظر پیدا نشد" in response.content.decode()
    assert "Traceback" not in response.content.decode()
    assert 'name="robots" content="noindex, nofollow"' in response.content.decode()
    assert "frame-ancestors 'none'" in response["Content-Security-Policy"]


@override_settings(DEBUG=False, ROOT_URLCONF="tests.error_urls")
def test_production_500_has_real_status_and_no_exception_details() -> None:
    response = Client(raise_request_exception=False).get("/trigger-server-error/")

    assert response.status_code == 500
    assert "مشکلی در سرور رخ داده است" in response.content.decode()
    assert "private-test-marker" not in response.content.decode()


@override_settings(DEBUG=False, ROOT_URLCONF="tests.error_urls")
def test_production_api_500_keeps_json_contract() -> None:
    response = Client(raise_request_exception=False).get("/api/trigger-server-error/")

    assert response.status_code == 500
    assert response.json()["error"]["code"] == "internal_error"
    assert "private-test-marker" not in response.content.decode()
