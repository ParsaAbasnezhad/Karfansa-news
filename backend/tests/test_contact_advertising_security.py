"""Exercise public form abuse limits and advertisement publication rules."""

from datetime import timedelta

import pytest
from django.core.cache import cache
from django.core.exceptions import ValidationError
from django.test import Client, override_settings
from django.utils import timezone

from apps.advertising.models import AdvertisementSlide
from apps.contact.models import ContactMessage

CONTACT = {
    "name": "Test Reader",
    "phone": "09121234567",
    "email": "reader@example.com",
    "subject": "سایر موارد",
    "message": "This is a test message.",
    "website": "",
}
LOCMEM_CACHE = {"default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"}}


@pytest.mark.django_db
@override_settings(CACHES=LOCMEM_CACHE)
def test_contact_requires_csrf_validates_email_and_limits_submissions() -> None:
    cache.clear()
    browser = Client(enforce_csrf_checks=True)
    path = "/api/v1/contact/"
    assert browser.post(path, CONTACT, content_type="application/json").status_code == 403

    browser.get("/api/v1/contact/csrf/")
    token = browser.cookies["csrftoken"].value
    headers = {"HTTP_X_CSRFTOKEN": token, "REMOTE_ADDR": "203.0.113.12"}
    invalid = browser.post(
        path, {**CONTACT, "email": "invalid-address"}, content_type="application/json", **headers
    )
    assert invalid.status_code == 422
    assert ContactMessage.objects.count() == 0

    results = [
        browser.post(path, CONTACT, content_type="application/json", **headers) for _ in range(6)
    ]
    assert [response.status_code for response in results] == [201, 201, 201, 201, 201, 429]
    assert ContactMessage.objects.count() == 5


@pytest.mark.django_db
def test_only_active_advertisements_within_publish_window_are_public(client: Client) -> None:
    now = timezone.now()
    visible = AdvertisementSlide.objects.create(
        title="Current", image_desktop="current.png", starts_at=now - timedelta(days=1)
    )
    AdvertisementSlide.objects.create(title="Hidden", image_desktop="hidden.png", is_active=False)
    AdvertisementSlide.objects.create(
        title="Future", image_desktop="future.png", starts_at=now + timedelta(days=1)
    )

    response = client.get("/api/v1/advertising/slides/")

    assert response.status_code == 200
    assert [item["id"] for item in response.json()["results"]] == [visible.pk]
    with pytest.raises(ValidationError):
        AdvertisementSlide(
            title="Unsafe", image_desktop="unsafe.png", button_url="javascript:alert(1)"
        ).full_clean()
