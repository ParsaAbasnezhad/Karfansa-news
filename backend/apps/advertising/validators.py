"""URL safety checks for public advertisement destinations."""

from urllib.parse import urlparse

from django.core.exceptions import ValidationError


BLOCKED_SCHEMES = frozenset({"javascript", "data", "vbscript", "file", "blob"})


def validate_safe_destination_url(value: str) -> None:
    """Allow site-relative paths and http(s) URLs; reject unsafe schemes."""
    text = (value or "").strip()
    if not text:
        return

    if text.startswith("/") and not text.startswith("//"):
        if any(ch in text for ch in ("\n", "\r", "\0")):
            raise ValidationError("آدرس مقصد معتبر نیست.", code="invalid")
        return

    parsed = urlparse(text)
    scheme = (parsed.scheme or "").lower()
    if scheme in BLOCKED_SCHEMES:
        raise ValidationError("این نوع پیوند مجاز نیست.", code="unsafe_scheme")
    if scheme not in {"http", "https"}:
        raise ValidationError("فقط پیوندهای http، https یا مسیر داخلی مجاز است.", code="invalid_scheme")
    if not parsed.netloc:
        raise ValidationError("آدرس مقصد معتبر نیست.", code="invalid")
