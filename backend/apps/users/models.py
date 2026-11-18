import uuid

from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """Existing username accounts remain valid; new contacts are claimed separately."""

    # Existing email values can be duplicated, so do not make AbstractUser.email unique.
    # Only newly registered/verified contacts are reserved in these nullable columns.
    normalized_email = models.EmailField(max_length=254, null=True, blank=True, unique=True)
    mobile = models.CharField(max_length=13, null=True, blank=True)  # noqa: DJ001 - legacy absence
    claimed_mobile = models.CharField(max_length=13, null=True, blank=True, unique=True)
    is_contact_signup = models.BooleanField(default=False)
    email_verified_at = models.DateTimeField(null=True, blank=True)
    mobile_verified_at = models.DateTimeField(null=True, blank=True)

    @property
    def email_verified(self) -> bool:
        return self.email_verified_at is not None

    @property
    def mobile_verified(self) -> bool:
        return self.mobile_verified_at is not None


class OTPChallenge(models.Model):
    """A short lived, single use challenge locked during verification."""

    class Purpose(models.TextChoices):
        REGISTRATION = "registration"
        LOGIN = "login"
        RESET = "reset"
        EMAIL_VERIFICATION = "email_verification"
        MOBILE_VERIFICATION = "mobile_verification"
        PASSWORD_CHANGE = "password_change"  # noqa: S105 - purpose label

    class Channel(models.TextChoices):
        EMAIL = "email"
        SMS = "sms"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="otp_challenges"
    )
    purpose = models.CharField(max_length=24, choices=Purpose.choices)
    channel = models.CharField(max_length=5, choices=Channel.choices)
    destination_digest = models.CharField(max_length=64)
    verifier = models.CharField(max_length=64)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    last_sent_at = models.DateTimeField()
    delivered_at = models.DateTimeField(null=True, blank=True)
    attempts = models.PositiveSmallIntegerField(default=0)
    consumed_at = models.DateTimeField(null=True, blank=True)
    invalidated_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        indexes = [models.Index(fields=["user", "purpose", "channel", "created_at"])]

    def __str__(self) -> str:
        return f"OTP challenge {self.pk} ({self.purpose})"


class ResetAuthorization(models.Model):
    """A one time capability issued only after a reset OTP is consumed."""

    token_digest = models.CharField(max_length=64, primary_key=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    consumed_at = models.DateTimeField(null=True, blank=True)

    def __str__(self) -> str:
        return f"Reset authorization for user {self.user_id}"
