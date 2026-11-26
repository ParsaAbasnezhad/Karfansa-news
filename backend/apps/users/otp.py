"""Database-backed OTP challenges and Redis-backed request limits.

The database row lock is the source of truth for single use. Redis counters are
additional abuse protection shared by all web workers.
"""

import logging
import secrets
import uuid
from collections.abc import Callable
from datetime import timedelta

from django.conf import settings
from django.core.cache import cache
from django.db import transaction
from django.http import HttpRequest
from django.utils import timezone
from django.utils.crypto import constant_time_compare, salted_hmac

from apps.common.client_ip import client_ip
from apps.common.exceptions import AppError, RateLimitedError

from .models import OTPChallenge, User
from .notifications import OTP_TTL_SECONDS, send_otp

logger = logging.getLogger(__name__)

OTP_TTL = timedelta(seconds=OTP_TTL_SECONDS)
RESEND_COOLDOWN = timedelta(seconds=60)
MAX_ATTEMPTS = 5


class InvalidChallengeError(AppError):
    code = "invalid_code"
    message = "The code is invalid or expired. Request a new code."


class DeliveryUnavailableError(AppError):
    status_code = 503
    code = "delivery_unavailable"
    message = "We could not send a code right now. Please try again later."


def _limit_key(action: str, category: str, value: str) -> str:
    digest = salted_hmac("auth-rate-limit", value, secret=settings.SECRET_KEY).hexdigest()
    return f"auth:{action}:{category}:{digest}"


def _increment_limit(key: str, limit: int, period: int) -> None:
    cache.add(key, 0, timeout=period)
    try:
        count = cache.incr(key)
    except ValueError:  # key expired between add and incr
        cache.add(key, 0, timeout=period)
        count = cache.incr(key)
    if count > limit:
        raise RateLimitedError("Too many attempts. Please try again later.")


def throttle(
    request: HttpRequest,
    action: str,
    *,
    identifier: str | None = None,
    user_id: int | None = None,
    include_ip: bool = True,
    challenge_id: str | None = None,
) -> None:
    if include_ip:
        ip = client_ip(request)
        _increment_limit(_limit_key(action, "ip", ip), 30, 900)
    if identifier:
        _increment_limit(_limit_key(action, "identifier", identifier), 10, 900)
    if user_id is not None:
        _increment_limit(_limit_key(action, "account", str(user_id)), 15, 900)
    if challenge_id:
        _increment_limit(_limit_key(action, "challenge", challenge_id.casefold()), 10, 900)


def _verifier(challenge_id: uuid.UUID, purpose: str, code: str) -> str:
    return salted_hmac(
        "auth-otp-verifier",
        f"{challenge_id}:{purpose}:{code}",
        secret=settings.SECRET_KEY,
    ).hexdigest()


def _destination_digest(destination: str) -> str:
    return salted_hmac(
        "auth-otp-destination", destination.strip().casefold(), secret=settings.SECRET_KEY
    ).hexdigest()


def _enqueue(challenge_id: str) -> None:
    from .tasks import enqueue_otp_challenge

    if not enqueue_otp_challenge(challenge_id):
        raise DeliveryUnavailableError()


def _fake_key(challenge_id: str) -> str:
    return f"auth:fake-challenge:{challenge_id.casefold()}"


def fake_challenge_id() -> str:
    """Queue the same worker operation for an ineligible public request."""
    challenge_id = str(uuid.uuid4())
    cache.set(_fake_key(challenge_id), timezone.now().timestamp(), timeout=300)
    _enqueue(challenge_id)
    return challenge_id


def resend_fake_challenge(challenge_id: str) -> str:
    issued_at = cache.get(_fake_key(challenge_id))
    if issued_at is not None and timezone.now().timestamp() - issued_at < 60:
        _enqueue(str(uuid.uuid4()))
        return challenge_id
    return fake_challenge_id()


def enqueue_dummy_challenge() -> None:
    """Match a real cooldown request's broker work without sending a code."""
    _enqueue(str(uuid.uuid4()))


def issue_challenge(
    request: HttpRequest,
    user: User,
    purpose: str,
    channel: str,
    *,
    identifier: str,
    async_delivery: bool = False,
) -> OTPChallenge:
    throttle(request, f"issue-{purpose}", identifier=identifier, user_id=user.pk)
    now = timezone.now()
    with transaction.atomic():
        User.objects.select_for_update().get(pk=user.pk)
        active = OTPChallenge.objects.filter(
            user=user,
            purpose=purpose,
            channel=channel,
            consumed_at__isnull=True,
            invalidated_at__isnull=True,
        )
        latest = active.order_by("-last_sent_at").first()
        if latest and latest.last_sent_at + RESEND_COOLDOWN > now:
            raise RateLimitedError("Please wait before requesting another code.")
        active.update(invalidated_at=now)
        challenge_id = uuid.uuid4()
        code = "" if async_delivery else f"{secrets.randbelow(1_000_000):06d}"

        challenge = OTPChallenge.objects.create(
            id=challenge_id,
            user=user,
            purpose=purpose,
            channel=channel,
            destination_digest=_destination_digest(identifier),
            verifier="" if async_delivery else _verifier(challenge_id, purpose, code),
            expires_at=now + OTP_TTL,
            last_sent_at=now,
        )

    try:
        if async_delivery:
            _enqueue(str(challenge.pk))
        else:
            send_otp(destination=identifier, channel=channel, code=code, purpose=purpose)
            OTPChallenge.objects.filter(pk=challenge.pk).update(delivered_at=timezone.now())
    except Exception as exc:
        OTPChallenge.objects.filter(pk=challenge.pk).update(invalidated_at=timezone.now())
        logger.warning("auth_otp_delivery_failed", extra={"user_id": user.pk, "purpose": purpose})
        raise DeliveryUnavailableError() from exc
    return challenge


def generate_and_dispatch_challenge(challenge_id: str) -> None:
    """Worker entry point: code exists only in this process during delivery."""
    try:
        parsed_id = uuid.UUID(challenge_id)
    except (ValueError, AttributeError):
        return
    user_id = OTPChallenge.objects.filter(pk=parsed_id).values_list("user_id", flat=True).first()
    if user_id is None:
        return
    with transaction.atomic():
        user = User.objects.select_for_update().filter(pk=user_id).first()
        challenge = OTPChallenge.objects.select_for_update().filter(pk=parsed_id).first()
        if user is None or challenge is None or challenge.user_id != user.pk:
            return
        now = timezone.now()
        terminal = (
            challenge.invalidated_at
            or challenge.consumed_at
            or challenge.delivered_at
            or challenge.expires_at <= now
        )
        if terminal:
            return
        if challenge.channel == OTPChallenge.Channel.EMAIL:
            destination = user.email
        else:
            destination = user.mobile or ""
        digest = _destination_digest(destination)
        if not constant_time_compare(challenge.destination_digest, digest):
            challenge.invalidated_at = now
            challenge.save(update_fields=["invalidated_at"])
            return

        code = f"{secrets.randbelow(1_000_000):06d}"

        try:
            send_otp(
                destination=destination,
                channel=challenge.channel,
                code=code,
                purpose=challenge.purpose,
            )
        except Exception:
            challenge.invalidated_at = timezone.now()
            challenge.save(update_fields=["invalidated_at"])
            logger.warning(
                "auth_otp_delivery_failed", extra={"user_id": user_id, "purpose": challenge.purpose}
            )
            return
        now = timezone.now()
        challenge.verifier = _verifier(challenge.id, challenge.purpose, code)
        challenge.delivered_at = now
        challenge.expires_at = now + OTP_TTL
        challenge.save(update_fields=["verifier", "delivered_at", "expires_at"])


def consume_challenge(
    request: HttpRequest,
    challenge_id: str,
    code: str,
    purpose: str,
    on_success: Callable[[OTPChallenge], None] | None = None,
) -> User:
    throttle(request, f"verify-{purpose}", challenge_id=challenge_id)
    try:
        parsed_id = uuid.UUID(challenge_id)
    except (ValueError, AttributeError) as exc:
        raise InvalidChallengeError() from exc

    # Lock user first, then challenge. Issuance takes locks in the same order.
    user_id = OTPChallenge.objects.filter(pk=parsed_id).values_list("user_id", flat=True).first()
    if user_id is None:
        raise InvalidChallengeError()

    user: User | None = None
    valid = False
    with transaction.atomic():
        user = User.objects.select_for_update().filter(pk=user_id).first()
        challenge = OTPChallenge.objects.select_for_update().filter(pk=parsed_id).first()
        if user is not None and challenge is not None and challenge.user_id == user.pk:
            identifier = (
                user.email
                if challenge.channel == OTPChallenge.Channel.EMAIL
                else (user.mobile or "")
            )
            try:
                throttle(
                    request,
                    f"verify-{purpose}",
                    identifier=identifier,
                    user_id=user.pk,
                    include_ip=False,
                )
            except RateLimitedError as exc:
                # Public verification must not reveal whether a challenge ID exists.
                raise InvalidChallengeError() from exc
            now = timezone.now()
            current_destination = (
                user.email
                if challenge.channel == OTPChallenge.Channel.EMAIL
                else (user.mobile or "")
            )
            if (
                challenge.purpose == purpose
                and challenge.consumed_at is None
                and challenge.invalidated_at is None
                and challenge.delivered_at is not None
                and challenge.expires_at > now
                and challenge.attempts < MAX_ATTEMPTS
                and constant_time_compare(
                    challenge.destination_digest, _destination_digest(current_destination)
                )
            ):
                if constant_time_compare(
                    challenge.verifier, _verifier(challenge.id, purpose, code)
                ):
                    challenge.consumed_at = now
                    challenge.save(update_fields=["consumed_at"])
                    if on_success is not None:
                        on_success(challenge)
                    valid = True
                else:
                    challenge.attempts += 1
                    if challenge.attempts >= MAX_ATTEMPTS:
                        challenge.invalidated_at = now
                    challenge.save(update_fields=["attempts", "invalidated_at"])
    if not valid or user is None:
        raise InvalidChallengeError()
    user.refresh_from_db()
    return user
