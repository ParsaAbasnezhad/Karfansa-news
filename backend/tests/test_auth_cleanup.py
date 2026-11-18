from datetime import timedelta

import pytest
from django.contrib.auth import get_user_model
from django.utils import timezone

from apps.users.models import OTPChallenge, ResetAuthorization
from apps.users.tasks import cleanup_security_records


@pytest.mark.django_db
def test_cleanup_removes_only_old_terminal_security_records() -> None:
    user = get_user_model().objects.create_user(username="cleanup-reader", password="safe-password")
    now = timezone.now()
    stale = now - timedelta(days=8)

    expired = OTPChallenge.objects.create(
        user=user,
        purpose=OTPChallenge.Purpose.LOGIN,
        channel=OTPChallenge.Channel.EMAIL,
        destination_digest="a" * 64,
        verifier="a" * 64,
        expires_at=stale + timedelta(minutes=5),
        last_sent_at=stale,
    )
    active = OTPChallenge.objects.create(
        user=user,
        purpose=OTPChallenge.Purpose.LOGIN,
        channel=OTPChallenge.Channel.EMAIL,
        destination_digest="b" * 64,
        verifier="b" * 64,
        expires_at=now + timedelta(days=1),
        last_sent_at=stale,
    )
    recent_consumed = OTPChallenge.objects.create(
        user=user,
        purpose=OTPChallenge.Purpose.LOGIN,
        channel=OTPChallenge.Channel.EMAIL,
        destination_digest="c" * 64,
        verifier="c" * 64,
        expires_at=now + timedelta(minutes=5),
        last_sent_at=now,
        consumed_at=now,
    )
    OTPChallenge.objects.filter(pk__in=[expired.pk, active.pk]).update(created_at=stale)

    stale_reset = ResetAuthorization.objects.create(
        token_digest="d" * 64,
        user=user,
        expires_at=stale + timedelta(minutes=10),
    )
    live_reset = ResetAuthorization.objects.create(
        token_digest="e" * 64,
        user=user,
        expires_at=now + timedelta(minutes=10),
    )
    ResetAuthorization.objects.filter(pk=stale_reset.pk).update(created_at=stale)

    abandoned = get_user_model().objects.create_user(
        username="abandoned-reader",
        password="safe-password",
        is_active=False,
        is_contact_signup=True,
        normalized_email="abandoned@example.com",
        claimed_mobile="+989121234567",
    )
    verified = get_user_model().objects.create_user(
        username="verified-reader",
        password="safe-password",
        is_active=False,
        is_contact_signup=True,
        normalized_email="verified@example.com",
        email_verified_at=now,
    )
    get_user_model().objects.filter(pk__in=[abandoned.pk, verified.pk]).update(date_joined=stale)

    result = cleanup_security_records()

    assert result == {
        "challenges_deleted": 1,
        "authorizations_deleted": 1,
        "claims_released": 1,
    }
    assert not OTPChallenge.objects.filter(pk=expired.pk).exists()
    assert OTPChallenge.objects.filter(pk=active.pk).exists()
    assert OTPChallenge.objects.filter(pk=recent_consumed.pk).exists()
    assert not ResetAuthorization.objects.filter(pk=stale_reset.pk).exists()
    assert ResetAuthorization.objects.filter(pk=live_reset.pk).exists()
    assert get_user_model().objects.filter(pk=user.pk).exists()
    abandoned.refresh_from_db()
    verified.refresh_from_db()
    assert abandoned.normalized_email is None
    assert abandoned.claimed_mobile is None
    assert verified.normalized_email == "verified@example.com"
