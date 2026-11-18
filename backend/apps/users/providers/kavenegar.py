"""Kavenegar SMS adapter using the official VerifyLookup and sms/send APIs.

Configure:
  SMS_PROVIDER_CLASS=apps.users.providers.kavenegar.KavenegarSmsProvider
  KAVENEGAR_API_KEY=<secret>
  KAVENEGAR_VERIFY_TEMPLATE=<approved panel template name>

OTP codes are delivered with VerifyLookup so the plaintext code is substituted
into a pre-approved template (%token). Free-form security notices use sms/send.
Credentials are read only from environment-backed Django settings.
"""

from __future__ import annotations

import logging
from typing import Any
from urllib.parse import urlencode

import requests
from django.conf import settings

logger = logging.getLogger(__name__)

_API_ROOT = "https://api.kavenegar.com/v1"
_TIMEOUT_SECONDS = 10


class KavenegarSmsProvider:
    """Production SMS adapter for Iranian mobile delivery via Kavenegar."""

    def __init__(self) -> None:
        self.api_key = str(getattr(settings, "KAVENEGAR_API_KEY", "") or "").strip()
        self.template = str(getattr(settings, "KAVENEGAR_VERIFY_TEMPLATE", "") or "").strip()
        self.sender = str(getattr(settings, "KAVENEGAR_SENDER", "") or "").strip()
        if not self.api_key:
            raise ValueError("KAVENEGAR_API_KEY is required for the Kavenegar adapter")

    def send_verification_code(self, *, destination: str, code: str, purpose: str) -> bool:
        """Send an OTP through VerifyLookup; return True only on HTTP return.status 200."""
        del purpose  # Template text owns the user-facing copy; purpose is audit-only upstream.
        if not self.template:
            logger.error("auth_kavenegar_template_missing")
            return False
        payload = {
            "receptor": _receptor(destination),
            "token": code,
            "template": self.template,
            "type": "sms",
        }
        return self._post("verify/lookup.json", payload)

    def send_sms(self, *, destination: str, message: str) -> bool:
        """Send a free-form notice through sms/send.json."""
        payload: dict[str, str] = {
            "receptor": _receptor(destination),
            "message": message,
        }
        if self.sender:
            payload["sender"] = self.sender
        return self._post("sms/send.json", payload)

    def _post(self, path: str, payload: dict[str, str]) -> bool:
        url = f"{_API_ROOT}/{self.api_key}/{path}"
        try:
            response = requests.post(
                url,
                data=urlencode(payload),
                headers={"Content-Type": "application/x-www-form-urlencoded"},
                timeout=_TIMEOUT_SECONDS,
            )
        except requests.RequestException:
            logger.warning("auth_kavenegar_request_failed", extra={"path": path})
            return False
        try:
            body: dict[str, Any] = response.json()
        except ValueError:
            logger.warning(
                "auth_kavenegar_invalid_response",
                extra={"path": path, "http_status": response.status_code},
            )
            return False
        status = ((body.get("return") or {}).get("status")) if isinstance(body, dict) else None
        if response.status_code == 200 and status == 200:
            return True
        logger.warning(
            "auth_kavenegar_rejected",
            extra={"path": path, "http_status": response.status_code, "provider_status": status},
        )
        return False


def _receptor(destination: str) -> str:
    """Normalize E.164 Iranian mobiles to the 09… form used in Kavenegar examples."""
    value = destination.strip()
    if value.startswith("+98"):
        return "0" + value[3:]
    if value.startswith("0098"):
        return "0" + value[4:]
    return value
