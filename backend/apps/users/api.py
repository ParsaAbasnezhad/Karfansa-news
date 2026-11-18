"""Session authentication endpoints for the existing v1 Ninja API."""

from django.contrib.auth import logout
from django.http import HttpRequest
from django.views.decorators.csrf import csrf_protect, ensure_csrf_cookie
from ninja import Router, Status
from ninja.decorators import decorate_view

from . import services
from .models import User
from .schemas import (
    AuthOut,
    ChallengeCodeIn,
    ChallengeOut,
    ChangePasswordIn,
    ContactMethodIn,
    IdentifierIn,
    MessageOut,
    PasswordLoginIn,
    ProfileUpdateIn,
    RegisterIn,
    ResendIn,
    ResetPasswordIn,
    ResetTokenOut,
    UserOut,
)

router = Router(tags=["auth"])


def _user_out(user: User) -> UserOut:
    return UserOut(
        id=user.pk,
        username=user.username,
        first_name=user.first_name,
        last_name=user.last_name,
        email=user.email,
        mobile=user.mobile,
        email_verified=user.email_verified,
        mobile_verified=user.mobile_verified,
        date_joined=user.date_joined.isoformat(),
    )


@router.get("/csrf/", response=MessageOut, operation_id="auth_csrf")
@decorate_view(ensure_csrf_cookie)
def csrf(request: HttpRequest) -> MessageOut:
    return MessageOut(message="ok")


@router.post("/register/", response={201: ChallengeOut}, operation_id="auth_register")
@decorate_view(csrf_protect)
def register(request: HttpRequest, payload: RegisterIn) -> Status[ChallengeOut]:
    challenge_id = services.register(request, payload)
    return Status(
        201,
        ChallengeOut(
            message="If eligible, a verification code will be sent.", challenge_id=challenge_id
        ),
    )


@router.post("/verify-registration/", response=AuthOut, operation_id="auth_verify_registration")
@decorate_view(csrf_protect)
def verify_registration(request: HttpRequest, payload: ChallengeCodeIn) -> AuthOut:
    user = services.verify_registration(request, payload.challenge_id, payload.code)
    return AuthOut(user=_user_out(user))


@router.post("/login/", response=AuthOut, operation_id="auth_login")
@decorate_view(csrf_protect)
def login(request: HttpRequest, payload: PasswordLoginIn) -> AuthOut:
    user = services.password_login(request, payload.identifier, payload.password)
    return AuthOut(user=_user_out(user))


@router.post("/request-login-otp/", response=ChallengeOut, operation_id="auth_request_login_otp")
@decorate_view(csrf_protect)
def request_login_otp(request: HttpRequest, payload: IdentifierIn) -> ChallengeOut:
    challenge_id = services.request_login_code(request, payload.identifier)
    return ChallengeOut(
        message="If eligible, a sign-in code will be sent.", challenge_id=challenge_id
    )


@router.post("/verify-login-otp/", response=AuthOut, operation_id="auth_verify_login_otp")
@decorate_view(csrf_protect)
def verify_login_otp(request: HttpRequest, payload: ChallengeCodeIn) -> AuthOut:
    user = services.verify_login_code(request, payload.challenge_id, payload.code)
    return AuthOut(user=_user_out(user))


@router.post("/resend-otp/", response=ChallengeOut, operation_id="auth_resend_otp")
@decorate_view(csrf_protect)
def resend_otp(request: HttpRequest, payload: ResendIn) -> ChallengeOut:
    challenge_id = services.resend_code(request, payload.challenge_id)
    return ChallengeOut(message="If eligible, a new code will be sent.", challenge_id=challenge_id)


@router.post("/forgot-password/", response=ChallengeOut, operation_id="auth_forgot_password")
@decorate_view(csrf_protect)
def forgot_password(request: HttpRequest, payload: IdentifierIn) -> ChallengeOut:
    challenge_id = services.forgot_password(request, payload.identifier)
    return ChallengeOut(
        message="If eligible, a password reset code will be sent.", challenge_id=challenge_id
    )


@router.post("/verify-reset-otp/", response=ResetTokenOut, operation_id="auth_verify_reset_otp")
@decorate_view(csrf_protect)
def verify_reset_otp(request: HttpRequest, payload: ChallengeCodeIn) -> ResetTokenOut:
    token = services.verify_reset_code(request, payload.challenge_id, payload.code)
    return ResetTokenOut(reset_token=token)


@router.post("/reset-password/", response=MessageOut, operation_id="auth_reset_password")
@decorate_view(csrf_protect)
def reset_password(request: HttpRequest, payload: ResetPasswordIn) -> MessageOut:
    services.reset_password(
        request, payload.reset_token, payload.new_password, payload.password_confirmation
    )
    return MessageOut(message="Password updated. Please sign in again.")


@router.post(
    "/request-change-password-otp/",
    response=ChallengeOut,
    operation_id="auth_request_change_password_otp",
)
@decorate_view(csrf_protect)
def request_change_password_otp(request: HttpRequest) -> ChallengeOut:
    challenge_id = services.request_password_change_code(request)
    return ChallengeOut(
        message="A code was sent to your verified contact.", challenge_id=challenge_id
    )


@router.post("/change-password/", response=MessageOut, operation_id="auth_change_password")
@decorate_view(csrf_protect)
def change_password(request: HttpRequest, payload: ChangePasswordIn) -> MessageOut:
    services.change_password(
        request,
        payload.challenge_id,
        payload.code,
        payload.new_password,
        payload.password_confirmation,
    )
    return MessageOut(message="Password updated.")


@router.post(
    "/request-contact-verification/",
    response=ChallengeOut,
    operation_id="auth_request_contact_verification",
)
@decorate_view(csrf_protect)
def request_contact_verification(request: HttpRequest, payload: ContactMethodIn) -> ChallengeOut:
    challenge_id = services.request_contact_verification(request, payload.method)
    return ChallengeOut(message="A verification code was sent.", challenge_id=challenge_id)


@router.post("/verify-contact/", response=AuthOut, operation_id="auth_verify_contact")
@decorate_view(csrf_protect)
def verify_contact(request: HttpRequest, payload: ChallengeCodeIn) -> AuthOut:
    user = services.verify_contact(request, payload.challenge_id, payload.code)
    return AuthOut(user=_user_out(user))


@router.post("/logout/", response=MessageOut, operation_id="auth_logout")
@decorate_view(csrf_protect)
def logout_view(request: HttpRequest) -> MessageOut:
    logout(request)
    return MessageOut(message="Signed out.")


@router.get("/me/", response=AuthOut, operation_id="auth_me")
def me(request: HttpRequest) -> AuthOut:
    return AuthOut(user=_user_out(services.current_user(request)))


@router.patch("/me/", response=AuthOut, operation_id="auth_update_profile")
@decorate_view(csrf_protect)
def update_profile(request: HttpRequest, payload: ProfileUpdateIn) -> AuthOut:
    user = services.current_user(request)
    user.first_name = payload.first_name
    user.last_name = payload.last_name
    user.save(update_fields=["first_name", "last_name"])
    return AuthOut(user=_user_out(user))
