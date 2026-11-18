"""Resolve the client address only from explicitly trusted proxy metadata."""

from ipaddress import ip_address

from django.conf import settings
from django.http import HttpRequest


def client_ip(request: HttpRequest) -> str:
    if getattr(settings, "TRUST_X_REAL_IP", False):
        value = request.META.get("HTTP_X_REAL_IP", "")
        try:
            # A single address is required. Lists such as X-Forwarded-For are
            # deliberately rejected because their trust boundary is ambiguous.
            return str(ip_address(value))
        except ValueError:
            pass
    remote = request.META.get("REMOTE_ADDR")
    return remote if isinstance(remote, str) and remote else "unknown"
