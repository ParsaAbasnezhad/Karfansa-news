"""Validate newly uploaded staff images before they reach media storage."""

from __future__ import annotations

from pathlib import Path

from django.core.exceptions import ValidationError
from django.core.files import File
from PIL import Image, UnidentifiedImageError

MAX_IMAGE_BYTES = 10 * 1024 * 1024
MAX_IMAGE_PIXELS = 25_000_000
ALLOWED_IMAGE_EXTENSIONS = {
    "JPEG": {".jpg", ".jpeg"},
    "PNG": {".png"},
    "WEBP": {".webp"},
    "GIF": {".gif"},
    "AVIF": {".avif"},
}


def validate_staff_image(value: File[bytes]) -> None:
    """Check the content of new uploads without reopening existing media files."""
    if getattr(value, "_committed", False):
        return

    if value.size > MAX_IMAGE_BYTES:
        raise ValidationError("حجم تصویر باید حداکثر ده مگابایت باشد.")

    upload = getattr(value, "file", value)
    position = upload.tell()
    try:
        upload.seek(0)
        with Image.open(upload) as image:
            image_format = image.format or ""
            width, height = image.size
            extension = Path(value.name or "").suffix.lower()
            if extension not in ALLOWED_IMAGE_EXTENSIONS.get(image_format, set()):
                raise ValidationError("فرمت تصویر یا پسوند فایل مجاز نیست.")
            if width <= 0 or height <= 0 or width * height > MAX_IMAGE_PIXELS:
                raise ValidationError("ابعاد تصویر بیش از حد مجاز است.")
            image.verify()

        upload.seek(0)
        with Image.open(upload) as image:
            image.load()
    except (OSError, SyntaxError, UnidentifiedImageError, Image.DecompressionBombError) as exc:
        raise ValidationError("فایل تصویر معتبر یا سالم نیست.") from exc
    finally:
        upload.seek(position)
