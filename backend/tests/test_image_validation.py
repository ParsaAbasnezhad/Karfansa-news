"""Staff image uploads are checked without reopening existing media."""

from io import BytesIO

import pytest
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.forms import modelform_factory
from PIL import Image

from apps.advertising.models import AdvertisementSlide
from apps.common import image_validation
from apps.editorial.models import EditorialArticle, EditorialImage
from apps.pages.models import AboutPage, AboutTeamMember

IMAGE_FIELDS = [
    (AdvertisementSlide, "image_desktop"),
    (AdvertisementSlide, "image_mobile"),
    (EditorialArticle, "featured_image"),
    (EditorialImage, "image"),
    (AboutPage, "hero_image"),
    (AboutPage, "mission_image"),
    (AboutTeamMember, "photo"),
]


def png_upload(name="image.png", size=(4, 4)):
    buffer = BytesIO()
    Image.new("RGB", size, "#2c6484").save(buffer, format="PNG")
    return SimpleUploadedFile(name, buffer.getvalue(), content_type="image/png")


@pytest.mark.parametrize(("model", "field_name"), IMAGE_FIELDS)
def test_each_staff_image_field_validates_new_file_content(model, field_name):
    field = model._meta.get_field(field_name)
    assert image_validation.validate_staff_image in field.validators
    field.clean(png_upload(), model())
    with pytest.raises(ValidationError):
        field.clean(
            SimpleUploadedFile("image.png", b"not an image", content_type="image/png"),
            model(),
        )


def test_image_limits_and_extension_match_actual_format(monkeypatch):
    with pytest.raises(ValidationError, match="پسوند"):
        image_validation.validate_staff_image(png_upload("image.jpg"))

    monkeypatch.setattr(image_validation, "MAX_IMAGE_BYTES", 20)
    with pytest.raises(ValidationError, match="حجم"):
        image_validation.validate_staff_image(png_upload())

    monkeypatch.setattr(image_validation, "MAX_IMAGE_BYTES", 10 * 1024 * 1024)
    monkeypatch.setattr(image_validation, "MAX_IMAGE_PIXELS", 10)
    with pytest.raises(ValidationError, match="ابعاد"):
        image_validation.validate_staff_image(png_upload())


def test_truncated_image_is_rejected():
    valid_bytes = png_upload().read()
    truncated = SimpleUploadedFile("image.png", valid_bytes[:-12], content_type="image/png")
    with pytest.raises(ValidationError, match="سالم"):
        image_validation.validate_staff_image(truncated)


def test_admin_model_form_rejects_mismatched_image_content_and_extension():
    form_class = modelform_factory(AdvertisementSlide, fields=("title", "image_desktop"))
    form = form_class(
        {"title": "New slide"},
        {"image_desktop": png_upload("disguised.jpg")},
    )

    assert not form.is_valid()
    assert "image_desktop" in form.errors


@pytest.mark.django_db
def test_unrelated_admin_edit_preserves_existing_image_without_reopening_storage():
    slide = AdvertisementSlide.objects.create(
        title="Existing slide", image_desktop="advertising/slides/old-image.bmp"
    )
    form_class = modelform_factory(AdvertisementSlide, fields=("title", "image_desktop"))
    form = form_class({"title": "Updated slide"}, instance=slide)

    assert form.is_valid(), form.errors
    form.save()
    slide.refresh_from_db()
    assert slide.title == "Updated slide"
    assert slide.image_desktop.name == "advertising/slides/old-image.bmp"
