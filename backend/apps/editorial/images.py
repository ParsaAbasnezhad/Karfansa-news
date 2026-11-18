"""Create bounded responsive derivatives when staff upload an image."""

import io
import logging
from pathlib import PurePosixPath

from django.core.files.base import ContentFile
from PIL import Image, ImageOps

logger = logging.getLogger(__name__)
TARGET_WIDTHS = (480, 960, 1600)


def create_webp_variants(field) -> dict[str, str]:
    if not field:
        return {}
    variants: dict[str, str] = {}
    try:
        field.open("rb")
        with Image.open(field.file) as source:
            source.load()
            original = ImageOps.exif_transpose(source)
            if original.mode not in {"RGB", "RGBA"}:
                original = original.convert("RGBA" if "A" in original.getbands() else "RGB")
            widths = sorted({min(original.width, target) for target in TARGET_WIDTHS})
            for width in widths:
                resized = original.copy()
                if width < original.width:
                    resized.thumbnail((width, original.height), Image.Resampling.LANCZOS)
                output = io.BytesIO()
                resized.save(output, format="WEBP", quality=82, method=4)
                original_name = PurePosixPath(field.name)
                name = str(original_name.with_suffix("")) + f"-{resized.width}.webp"
                stored = field.storage.save(name, ContentFile(output.getvalue()))
                variants[str(resized.width)] = stored
    except (OSError, ValueError):
        logger.exception("Could not create editorial image variants", extra={"image": field.name})
    finally:
        field.close()
    return variants
