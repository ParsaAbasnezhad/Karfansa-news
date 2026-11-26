from django.apps import AppConfig
from django.conf import settings

from apps.users.notifications import validate_sms_backend_settings


class UsersConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.users"

    def ready(self) -> None:
        validate_sms_backend_settings(
            debug=settings.DEBUG,
            backend=getattr(settings, "SMS_BACKEND", "provider"),
        )
