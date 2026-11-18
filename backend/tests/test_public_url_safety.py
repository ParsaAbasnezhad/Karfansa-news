"""Do not publish executable links even if legacy rows bypassed form validation."""

import pytest
from django.core.exceptions import ValidationError
from django.test import Client

from apps.advertising.models import AdvertisementSlide
from apps.advertising.validators import safe_destination_url, validate_safe_destination_url
from apps.pages.models import AboutPage, ContactPage


@pytest.mark.parametrize(
    "value",
    [
        "javascript:alert(1)",
        "//elsewhere.example",
        "/\\elsewhere.example",
        "https://user:pass@elsewhere.example/path",
        "https://ok.test\n@bad.test",
    ],
)
def test_unsafe_destinations_are_rejected(value: str) -> None:
    with pytest.raises(ValidationError):
        validate_safe_destination_url(value)
    assert safe_destination_url(value) == ""


@pytest.mark.django_db
def test_public_apis_fail_closed_on_unsafe_stored_destinations(client: Client) -> None:
    slide = AdvertisementSlide.objects.create(title="Test", image_desktop="sample.png")
    AdvertisementSlide.objects.filter(pk=slide.pk).update(button_url="javascript:alert(1)")
    about = AboutPage.load()
    AboutPage.objects.filter(pk=about.pk).update(primary_cta_url="javascript:alert(1)")
    contact = ContactPage.load()
    ContactPage.objects.filter(pk=contact.pk).update(map_url="javascript:alert(1)")

    assert client.get("/api/v1/advertising/slides/").json()["results"][0]["button_url"] == ""
    assert client.get("/api/v1/pages/about/").json()["primary_cta_url"] == ""
    assert client.get("/api/v1/pages/contact/").json()["map_url"] == ""
