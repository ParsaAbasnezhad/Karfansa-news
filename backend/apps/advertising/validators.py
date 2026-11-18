"""URL safety checks for public advertisement destinations."""

from urllib.parse import urlparse

from django.core.exceptions import ValidationError

BLOCKED_SCHEMES = frozenset({"javascript", "data", "vbscript", "file", "blob"})


def validate_safe_destination_url(value: str) -> None:
    """Allow site-relative paths and http(s) URLs; reject unsafe schemes."""
    text = (value or "").strip()
    if not text:
        return
    if "\\" in text or any(ch.isspace() or ord(ch) < 32 for ch in text):
        raise ValidationError("آدرس مقصد معتبر نیست.", code="invalid")

    if text.startswith("/") and not text.startswith("//"):
        if any(ch in text for ch in ("\n", "\r", "\0")):
            raise ValidationError("آدرس مقصد معتبر نیست.", code="invalid")
        return

    try:
        parsed = urlparse(text)
    except ValueError as exc:
        raise ValidationError("آدرس مقصد معتبر نیست.", code="invalid") from exc
    scheme = (parsed.scheme or "").lower()
    if scheme in BLOCKED_SCHEMES:
        raise ValidationError("این نوع پیوند مجاز نیست.", code="unsafe_scheme")
    if scheme not in {"http", "https"}:
        raise ValidationError(
            "فقط پیوندهای http، https یا مسیر داخلی مجاز است.", code="invalid_scheme"
        )
    if not parsed.hostname or parsed.username or parsed.password:
        raise ValidationError("آدرس مقصد معتبر نیست.", code="invalid")
    try:
        _ = parsed.port
    except ValueError as exc:
        raise ValidationError("آدرس مقصد معتبر نیست.", code="invalid") from exc


def safe_destination_url(value: str) -> str:
    """Fail closed when legacy or direct database writes contain an unsafe link."""
    try:
        validate_safe_destination_url(value)
    except ValidationError:
        return ""
    return value.strip()
