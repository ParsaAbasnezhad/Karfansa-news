"""Fail closed on source URLs written by feeds or legacy database rows."""

from urllib.parse import urlsplit

from django import template

from apps.advertising.validators import safe_destination_url

register = template.Library()


@register.filter
def safe_external_url(value: str) -> str:
    clean = safe_destination_url(value)
    return clean if urlsplit(clean).scheme in {"http", "https"} else ""
