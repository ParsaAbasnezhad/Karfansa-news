"""Registration, sign-in and account security workflows."""

import hashlib
import secrets
import time
import uuid
from collections.abc import Callable
from datetime import timedelta
from functools import wraps

from django.conf import settings
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import IntegrityError, transaction
from django.db.models import Q
from django.http import HttpRequest
from django.utils import timezone

from apps.common.exceptions import AppError, RateLimitedError

from .models import OTPChallenge, ResetAuthorization, User
from .notifications import queue_security_notice
from .otp import (
    DeliveryUnavailableError,
    InvalidChallengeError,
    consume_challenge,
    enqueue_dummy_challenge,
    fake_challenge_id,
    issue_challenge,
    resend_fake_challenge,
    throttle,
)
from .schemas import RegisterIn, normalize_email, normalize_mobile


def public_response_floor[**P, R](func: Callable[P, R]) -> Callable[P, R]:
    """Reduce timing differences between eligible and ineligible public requests."""

    @wraps(func)
    def wrapped(*args: P.args, **kwargs: P.kwargs) -> R:
        started = time.monotonic()
        try:
            return func(*args, **kwargs)
        finally:
            floor = getattr(settings, "AUTH_PUBLIC_RESPONSE_FLOOR_SECONDS", 0.75)
            time.sleep(max(0.0, floor - (time.monotonic() - started)))

    return wrapped


class InvalidCredentialsError(AppError):
    status_code = 401
    code = "invalid_credentials"
    message = "Invalid credentials."


class AuthenticationRequiredError(AppError):
    status_code = 401
    code = "authentication_required"
    message = "Sign in to continue."


class InvalidResetAuthorizationError(AppError):
    code = "invalid_reset_authorization"
    message = "Reset authorization has expired. Request a new code."


def current_user(request: HttpRequest) -> User:
    user = request.user
    if not user.is_authenticated or not user.is_active:
        raise AuthenticationRequiredError()
    return user


def _validate_new_password(password: str, confirmation: str, user: User) -> None:
    if password != confirmation:
        raise AppError("Passwords do not match.")
    try:
        validate_password(password, user=user)
    except DjangoValidationError as exc:
        raise AppError("Choose a stronger password.", details=exc.messages) from exc
    if user.pk and user.check_password(password):
        raise AppError("Choose a password you have not used for this account.")


def _matching_users(identifier: str, *, allow_username: bool = False) -> tuple[list[User], str]:
    value = identifier.strip()
    if "@" in value:
        try:
            email = normalize_email(value)
        except ValueError:
            return [], "email"
        claimed = list(User.objects.filter(normalized_email=email)[:2])
        if claimed:
            return claimed, "email"
        legacy = list(User.objects.filter(email__iexact=email, is_contact_signup=False)[:2])
        return legacy, "email"
    try:
        mobile = normalize_mobile(value)
    except ValueError:
        if allow_username:
            users = list(User.objects.filter(username=value, is_contact_signup=False)[:2])
            return users, "username"
        return [], "mobile"
    return list(User.objects.filter(claimed_mobile=mobile)[:2]), "mobile"


def _eligible_user(
    identifier: str, *, allow_legacy_password: bool = False
) -> tuple[User | None, str]:
    users, kind = _matching_users(identifier, allow_username=allow_legacy_password)
    if len(users) != 1:
        return None, kind
    user = users[0]
    if not user.is_active:
        return None, kind
    # Legacy username accounts predate verification and retain password sign-in.
    if (
        kind == "email"
        and not user.email_verified_at
        and not (allow_legacy_password and not user.is_contact_signup)
    ):
        return None, kind
    if kind == "mobile" and not user.mobile_verified_at:
        return None, kind
    return user, kind


def _contact(user: User, channel: str) -> str:
    return user.email if channel == OTPChallenge.Channel.EMAIL else (user.mobile or "")


@public_response_floor
def register(request: HttpRequest, payload: RegisterIn) -> str:
    throttle(request, "register", identifier=payload.email or payload.mobile)
    email = payload.email or ""
    mobile = payload.mobile
    channel = (
        OTPChallenge.Channel.EMAIL
        if payload.verification_method == "email"
        else OTPChallenge.Channel.SMS
    )
    new_user = User(
        username=f"u_{uuid.uuid4().hex}",
        first_name=payload.first_name,
        last_name=payload.last_name,
        email=email,
        normalized_email=email if channel == OTPChallenge.Channel.EMAIL else None,
        mobile=mobile,
        claimed_mobile=mobile if channel == OTPChallenge.Channel.SMS else None,
        is_contact_signup=True,
        is_active=False,
    )
    _validate_new_password(payload.password, payload.password_confirmation, new_user)
    email_conflict = Q(email__iexact=email, is_contact_signup=False)
    if channel == OTPChallenge.Channel.EMAIL:
        email_conflict |= Q(normalized_email=email)
    else:
        email_conflict |= Q(normalized_email=email, email_verified_at__isnull=False)
    mobile_conflict = Q(claimed_mobile=mobile)
    if channel == OTPChallenge.Channel.EMAIL:
        mobile_conflict &= Q(mobile_verified_at__isnull=False)
    conflicts = User.objects.filter(
        (email_conflict if email else Q(pk__in=[])) | (mobile_conflict if mobile else Q(pk__in=[]))
        | Q(is_contact_signup=True, is_active=False, email=email, mobile=mobile)
    )
    existing = list(conflicts[:2])
    created = False
    if existing:
        if (
            len(existing) != 1
            or existing[0].is_active
            or not existing[0].is_contact_signup
            or existing[0].email != email
            or existing[0].mobile != mobile
            or (channel == OTPChallenge.Channel.EMAIL and existing[0].normalized_email != email)
            or (channel == OTPChallenge.Channel.SMS and existing[0].claimed_mobile != mobile)
            or not existing[0].check_password(payload.password)
        ):
            return fake_challenge_id()
        user = existing[0]
    else:
        user = new_user
        user.set_password(payload.password)
        try:
            with transaction.atomic():
                user.save(force_insert=True)
        except IntegrityError:
            return fake_challenge_id()
        created = True

    try:
        challenge = issue_challenge(
            request,
            user,
            OTPChallenge.Purpose.REGISTRATION,
            channel,
            identifier=_contact(user, channel),
            async_delivery=True,
        )
    except Exception:
        # A failed delivery must not permanently reserve an unusable new account.
        if created:
            user.delete()
        raise
    return str(challenge.pk)


def verify_registration(request: HttpRequest, challenge_id: str, code: str) -> User:
    def activate(challenge: OTPChallenge) -> None:
        user = challenge.user
        now = timezone.now()
        if challenge.channel == OTPChallenge.Channel.EMAIL:
            user.email_verified_at = now
            user.save(update_fields=["email_verified_at"])
        else:
            user.mobile_verified_at = now
            user.save(update_fields=["mobile_verified_at"])
        user.is_active = True
        user.save(update_fields=["is_active"])

    user = consume_challenge(
        request, challenge_id, code, OTPChallenge.Purpose.REGISTRATION, activate
    )
    login(request, user, backend="django.contrib.auth.backends.ModelBackend")
    return user


def password_login(request: HttpRequest, identifier: str, password: str) -> User:
    throttle(request, "password-login", identifier=identifier.strip().casefold())
    user, _ = _eligible_user(identifier, allow_legacy_password=True)
    candidate = authenticate(
        request, username=user.username if user else "invalid-user", password=password
    )
    if candidate is None or user is None or candidate.pk != user.pk:
        raise InvalidCredentialsError()
    login(request, candidate)
    return candidate


@public_response_floor
def request_login_code(request: HttpRequest, identifier: str) -> str:
    throttle(request, "login-otp-request", identifier=identifier.strip().casefold())
    user, kind = _eligible_user(identifier)
    if user is None or kind == "username":
        return fake_challenge_id()
    channel = OTPChallenge.Channel.EMAIL if kind == "email" else OTPChallenge.Channel.SMS
    try:
        challenge = issue_challenge(
            request,
            user,
            OTPChallenge.Purpose.LOGIN,
            channel,
            identifier=_contact(user, channel),
            async_delivery=True,
        )
    except (RateLimitedError, DeliveryUnavailableError):
        return fake_challenge_id()
    return str(challenge.pk)


def verify_login_code(request: HttpRequest, challenge_id: str, code: str) -> User:
    user = consume_challenge(request, challenge_id, code, OTPChallenge.Purpose.LOGIN)
    if not user.is_active:
        raise InvalidChallengeError()
    login(request, user, backend="django.contrib.auth.backends.ModelBackend")
    return user


@public_response_floor
def resend_code(request: HttpRequest, challenge_id: str) -> str:
    throttle(request, "resend-otp")
    try:
        parsed_id = uuid.UUID(challenge_id)
    except (ValueError, AttributeError):
        return fake_challenge_id()
    old = OTPChallenge.objects.select_related("user").filter(pk=parsed_id).first()
    if old is None:
        return resend_fake_challenge(challenge_id)
    latest = OTPChallenge.objects.filter(
        user=old.user, purpose=old.purpose, channel=old.channel
    ).order_by("-last_sent_at").first()
    if old.consumed_at or old.invalidated_at or latest is None or latest.pk != old.pk:
        return resend_fake_challenge(challenge_id)
    if old.purpose == OTPChallenge.Purpose.REGISTRATION and old.user.is_active:
        return fake_challenge_id()
    if old.purpose == OTPChallenge.Purpose.REGISTRATION:
        if (
            old.channel == OTPChallenge.Channel.EMAIL
            and old.user.normalized_email != old.user.email
        ):
            return fake_challenge_id()
        if old.channel == OTPChallenge.Channel.SMS and old.user.claimed_mobile != old.user.mobile:
            return fake_challenge_id()
    if old.purpose != OTPChallenge.Purpose.REGISTRATION and not old.user.is_active:
        return fake_challenge_id()
    if old.last_sent_at + timedelta(seconds=60) > timezone.now():
        enqueue_dummy_challenge()
        return str(old.pk)
    try:
        challenge = issue_challenge(
            request,
            old.user,
            old.purpose,
            old.channel,
            identifier=_contact(old.user, old.channel),
            async_delivery=True,
        )
    except (RateLimitedError, DeliveryUnavailableError):
        return fake_challenge_id()
    return str(challenge.pk)


@public_response_floor
def forgot_password(request: HttpRequest, identifier: str) -> str:
    throttle(request, "forgot-password", identifier=identifier.strip().casefold())
    user, kind = _eligible_user(identifier)
    if user is None or kind == "username":
        return fake_challenge_id()
    channel = OTPChallenge.Channel.EMAIL if kind == "email" else OTPChallenge.Channel.SMS
    try:
        challenge = issue_challenge(
            request,
            user,
            OTPChallenge.Purpose.RESET,
            channel,
            identifier=_contact(user, channel),
            async_delivery=True,
        )
    except (RateLimitedError, DeliveryUnavailableError):
        return fake_challenge_id()
    return str(challenge.pk)


def verify_reset_code(request: HttpRequest, challenge_id: str, code: str) -> str:
    token = secrets.token_urlsafe(32)
    digest = hashlib.sha256(token.encode()).hexdigest()

    def authorize(challenge: OTPChallenge) -> None:
        ResetAuthorization.objects.create(
            token_digest=digest,
            user=challenge.user,
            expires_at=timezone.now() + timedelta(minutes=5),
        )

    consume_challenge(request, challenge_id, code, OTPChallenge.Purpose.RESET, authorize)
    return token


def reset_password(request: HttpRequest, token: str, password: str, confirmation: str) -> None:
    throttle(request, "reset-password")
    digest = hashlib.sha256(token.encode()).hexdigest()
    auth_user_id = (
        ResetAuthorization.objects.filter(token_digest=digest)
        .values_list("user_id", flat=True)
        .first()
    )
    if auth_user_id is None:
        raise InvalidResetAuthorizationError()
    with transaction.atomic():
        user = User.objects.select_for_update().get(pk=auth_user_id)
        authorization = (
            ResetAuthorization.objects.select_for_update().filter(token_digest=digest).first()
        )
        if (
            authorization is None
            or authorization.user_id != user.pk
            or authorization.consumed_at is not None
            or authorization.expires_at <= timezone.now()
        ):
            raise InvalidResetAuthorizationError()
        _validate_new_password(password, confirmation, user)
        user.set_password(password)
        user.save(update_fields=["password"])
        ResetAuthorization.objects.filter(user=user, consumed_at__isnull=True).update(
            consumed_at=timezone.now()
        )
        OTPChallenge.objects.filter(
            user=user, consumed_at__isnull=True, invalidated_at__isnull=True
        ).update(invalidated_at=timezone.now())
    logout(request)
    queue_security_notice(user.pk)


def request_password_change_code(request: HttpRequest) -> str:
    user = current_user(request)
    if user.email_verified_at and user.email:
        channel = OTPChallenge.Channel.EMAIL
    elif user.mobile_verified_at and user.mobile:
        channel = OTPChallenge.Channel.SMS
    else:
        raise AppError("Verify an email address or mobile number first.")
    challenge = issue_challenge(
        request,
        user,
        OTPChallenge.Purpose.PASSWORD_CHANGE,
        channel,
        identifier=_contact(user, channel),
    )
    return str(challenge.pk)


def change_password(
    request: HttpRequest, challenge_id: str, code: str, password: str, confirmation: str
) -> None:
    user = current_user(request)
    _validate_new_password(password, confirmation, user)

    def update_password(challenge: OTPChallenge) -> None:
        if challenge.user_id != user.pk:
            raise InvalidChallengeError()
        user.set_password(password)
        user.save(update_fields=["password"])
        ResetAuthorization.objects.filter(user=user, consumed_at__isnull=True).update(
            consumed_at=timezone.now()
        )
        OTPChallenge.objects.filter(
            user=user, consumed_at__isnull=True, invalidated_at__isnull=True
        ).update(invalidated_at=timezone.now())

    consume_challenge(
        request, challenge_id, code, OTPChallenge.Purpose.PASSWORD_CHANGE, update_password
    )
    update_session_auth_hash(request, user)
    queue_security_notice(user.pk)


def request_contact_verification(request: HttpRequest, method: str) -> str:
    user = current_user(request)
    if method == "email":
        if not user.email or user.email_verified_at:
            raise AppError("No unverified email address is available.")
        # Existing duplicate legacy emails cannot safely become verified claims.
        if (
            User.objects.filter(
                Q(normalized_email=user.email)
                | Q(email__iexact=user.email, is_contact_signup=False)
            )
            .exclude(pk=user.pk)
            .exists()
        ):
            raise AppError("This contact cannot be verified.")
        channel = OTPChallenge.Channel.EMAIL
        purpose = OTPChallenge.Purpose.EMAIL_VERIFICATION
    else:
        if not user.mobile or user.mobile_verified_at:
            raise AppError("No unverified mobile number is available.")
        if User.objects.filter(claimed_mobile=user.mobile).exclude(pk=user.pk).exists():
            raise AppError("This contact cannot be verified.")
        channel = OTPChallenge.Channel.SMS
        purpose = OTPChallenge.Purpose.MOBILE_VERIFICATION
    challenge = issue_challenge(request, user, purpose, channel, identifier=_contact(user, channel))
    return str(challenge.pk)


def verify_contact(request: HttpRequest, challenge_id: str, code: str) -> User:
    user = current_user(request)
    try:
        challenge = OTPChallenge.objects.only("purpose").get(pk=uuid.UUID(challenge_id))
    except (ValueError, OTPChallenge.DoesNotExist) as exc:
        raise InvalidChallengeError() from exc
    if challenge.purpose not in (
        OTPChallenge.Purpose.EMAIL_VERIFICATION,
        OTPChallenge.Purpose.MOBILE_VERIFICATION,
    ):
        raise InvalidChallengeError()

    def mark_verified(locked: OTPChallenge) -> None:
        if locked.user_id != user.pk:
            raise InvalidChallengeError()
        now = timezone.now()
        if locked.channel == OTPChallenge.Channel.EMAIL:
            if (
                User.objects.filter(
                    Q(normalized_email=user.email)
                    | Q(email__iexact=user.email, is_contact_signup=False)
                )
                .exclude(pk=user.pk)
                .exists()
            ):
                raise InvalidChallengeError()
            user.normalized_email = normalize_email(user.email)
            user.email_verified_at = now
            user.save(update_fields=["normalized_email", "email_verified_at"])
        else:
            if User.objects.filter(claimed_mobile=user.mobile).exclude(pk=user.pk).exists():
                raise InvalidChallengeError()
            user.claimed_mobile = user.mobile
            user.mobile_verified_at = now
            user.save(update_fields=["claimed_mobile", "mobile_verified_at"])

    try:
        return consume_challenge(request, challenge_id, code, challenge.purpose, mark_verified)
    except IntegrityError as exc:
        raise InvalidChallengeError() from exc
