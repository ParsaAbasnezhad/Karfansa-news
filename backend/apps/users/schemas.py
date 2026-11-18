"""Input and output contracts for the session based authentication API."""

import re
from typing import Literal

from django.core.exceptions import ValidationError as DjangoValidationError
from django.core.validators import validate_email
from ninja import Schema
from pydantic import Field, field_validator, model_validator

PERSIAN_DIGITS = str.maketrans("۰۱۲۳۴۵۶۷۸۹٠١٢٣٤٥٦٧٨٩", "01234567890123456789")


def normalize_mobile(value: str) -> str:
    compact = re.sub(r"[\s()\-]", "", value.translate(PERSIAN_DIGITS))
    if re.fullmatch(r"09[0-9]{9}", compact):
        compact = "+98" + compact[1:]
    elif re.fullmatch(r"00989[0-9]{9}", compact):
        compact = "+" + compact[2:]
    elif re.fullmatch(r"989[0-9]{9}", compact):
        compact = "+" + compact
    if not re.fullmatch(r"\+989[0-9]{9}", compact):
        raise ValueError("Enter a valid Iranian mobile number.")
    return compact


def normalize_email(value: str) -> str:
    address = value.strip().casefold()
    try:
        validate_email(address)
    except DjangoValidationError as exc:
        raise ValueError("Enter a valid email address.") from exc
    return address


class RegisterIn(Schema):
    first_name: str = Field(min_length=1, max_length=150)
    last_name: str = Field(min_length=1, max_length=150)
    email: str | None = None
    mobile: str | None = None
    password: str = Field(min_length=1, max_length=1024)
    password_confirmation: str
    verification_method: Literal["email", "sms"]

    @field_validator("first_name", "last_name")
    @classmethod
    def strip_name(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("This field is required.")
        return value

    @field_validator("email")
    @classmethod
    def valid_email(cls, value: str | None) -> str | None:
        return normalize_email(value) if value else None

    @field_validator("mobile")
    @classmethod
    def valid_mobile(cls, value: str | None) -> str | None:
        return normalize_mobile(value) if value else None

    @model_validator(mode="after")
    def contacts_and_confirmation(self) -> "RegisterIn":
        if not self.email and not self.mobile:
            raise ValueError("Provide an email address or mobile number.")
        if self.verification_method == "email" and not self.email:
            raise ValueError("Provide an email address for email verification.")
        if self.verification_method == "sms" and not self.mobile:
            raise ValueError("Provide a mobile number for SMS verification.")
        if self.password != self.password_confirmation:
            raise ValueError("Passwords do not match.")
        return self


class IdentifierIn(Schema):
    identifier: str = Field(min_length=3, max_length=254)


class PasswordLoginIn(IdentifierIn):
    password: str = Field(min_length=1)


class ChallengeCodeIn(Schema):
    challenge_id: str
    code: str = Field(pattern=r"^[0-9]{6}$")


class ResendIn(Schema):
    challenge_id: str


class ResetPasswordIn(Schema):
    reset_token: str = Field(min_length=32, max_length=256)
    new_password: str
    password_confirmation: str


class ChangePasswordIn(ChallengeCodeIn):
    new_password: str
    password_confirmation: str


class ContactMethodIn(Schema):
    method: Literal["email", "sms"]


class MessageOut(Schema):
    message: str


class ChallengeOut(MessageOut):
    challenge_id: str


class ResetTokenOut(Schema):
    reset_token: str


class UserOut(Schema):
    id: int
    username: str
    first_name: str
    last_name: str
    email: str
    mobile: str | None
    email_verified: bool
    mobile_verified: bool
    date_joined: str


class ProfileUpdateIn(Schema):
    first_name: str = Field(min_length=1, max_length=150)
    last_name: str = Field(min_length=1, max_length=150)

    @field_validator("first_name", "last_name")
    @classmethod
    def strip_profile_name(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("This field is required.")
        return value


class AuthOut(Schema):
    user: UserOut
