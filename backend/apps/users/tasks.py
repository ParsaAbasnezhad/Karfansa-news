"""Celery tasks for account notices that contain no authentication secret."""

import logging
from datetime import timedelta
from uuid import UUID

from celery import shared_task
from django.contrib.auth import get_user_model
from django.db.models import Q
from django.utils import timezone

from apps.users.models import OTPChallenge, ResetAuthorization
from apps.users.notifications import (
    DeliveryError,
    send_password_changed_notice,
    send_password_changed_sms_notice,
)

logger = logging.getLogger(__name__)


def enqueue_otp_challenge(challenge_id: UUID | str) -> bool:
    """Queue delivery by opaque ID only; public callers never dispatch inline."""
    try:
        dispatch_otp_challenge.apply_async(args=(str(challenge_id),), retry=False)
    except Exception:
        logger.warning("auth_otp_queue_failed")
        return False
    return True


@shared_task(name="apps.users.dispatch_otp_challenge")  # type: ignore[untyped-decorator]
def dispatch_otp_challenge(challenge_id: str) -> None:
    # Import lazily to avoid a cycle between the service and Celery task.
    from apps.users.otp import generate_and_dispatch_challenge

    generate_and_dispatch_challenge(challenge_id)


def deliver_notice_for_user(user_id: int) -> None:
    user = get_user_model().objects.filter(pk=user_id).first()
    if user is None:
        return
    if user.email_verified_at is not None and (user.normalized_email or user.email):
        send_password_changed_notice(destination=user.normalized_email or user.email)
    elif user.mobile_verified_at is not None:
        mobile = user.mobile or user.claimed_mobile
        if mobile:
            send_password_changed_sms_notice(destination=mobile)


@shared_task(  # type: ignore[untyped-decorator]
    name="apps.users.deliver_password_changed_notice",
    autoretry_for=(DeliveryError,),
    retry_backoff=True,
    retry_jitter=True,
    retry_kwargs={"max_retries": 3},
)
def deliver_password_changed_notice(user_id: int) -> None:
    deliver_notice_for_user(user_id)


@shared_task(name="apps.users.cleanup_security_records")  # type: ignore[untyped-decorator]
def cleanup_security_records() -> dict[str, int]:
    """Purge old terminal tokens and release stale, unverified signup claims."""
    now = timezone.now()
    cutoff = now - timedelta(days=7)
    challenges_deleted, _ = (
        OTPChallenge.objects.filter(created_at__lt=cutoff)
        .filter(
            Q(expires_at__lt=now) | Q(consumed_at__isnull=False) | Q(invalidated_at__isnull=False)
        )
        .delete()
    )
    authorizations_deleted, _ = (
        ResetAuthorization.objects.filter(created_at__lt=cutoff)
        .filter(Q(expires_at__lt=now) | Q(consumed_at__isnull=False))
        .delete()
    )
    claims_released = (
        get_user_model()
        .objects.filter(
            is_contact_signup=True,
            is_active=False,
            email_verified_at__isnull=True,
            mobile_verified_at__isnull=True,
            date_joined__lt=now - timedelta(days=1),
        )
        .filter(Q(normalized_email__isnull=False) | Q(claimed_mobile__isnull=False))
        .update(normalized_email=None, claimed_mobile=None)
    )
    return {
        "challenges_deleted": challenges_deleted,
        "authorizations_deleted": authorizations_deleted,
        "claims_released": claims_released,
    }
