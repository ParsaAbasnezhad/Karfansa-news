import re
from typing import Literal

from django.core.exceptions import ValidationError as DjangoValidationError
from django.core.validators import validate_email
from ninja import Schema
from pydantic import Field, field_validator


class ContactMessageIn(Schema):
    name: str = Field(min_length=2, max_length=120)
    phone: str = Field(min_length=8, max_length=24)
    email: str = Field(min_length=5, max_length=254)
    subject: Literal[
        "پیشنهاد سوژه",
        "اصلاح خبر",
        "همکاری رسانه‌ای",
        "تبلیغات",
        "پشتیبانی فنی",
        "سایر موارد",
    ]
    message: str = Field(min_length=10, max_length=3000)
    website: str = Field(default="", max_length=200)

    @field_validator("name", "phone", "email", "subject", "message", mode="before")
    @classmethod
    def strip_text(cls, value: str) -> str:
        if not isinstance(value, str):
            raise ValueError("مقدار واردشده باید متن باشد.")
        return value.strip()

    @field_validator("phone")
    @classmethod
    def normalize_phone(cls, value: str) -> str:
        translation = str.maketrans("۰۱۲۳۴۵۶۷۸۹٠١٢٣٤٥٦٧٨٩", "01234567890123456789")
        compact = re.sub(r"[\s()-]", "", value.translate(translation))
        if re.fullmatch(r"09\d{9}", compact):
            compact = f"+98{compact[1:]}"
        elif re.fullmatch(r"0098\d{10}", compact):
            compact = f"+{compact[2:]}"
        if not re.fullmatch(r"\+?[1-9]\d{7,14}", compact):
            raise ValueError("شماره موبایل معتبر وارد کنید.")
        return compact

    @field_validator("email")
    @classmethod
    def valid_email(cls, value: str) -> str:
        try:
            validate_email(value)
        except DjangoValidationError as exc:
            raise ValueError("آدرس ایمیل معتبر نیست.") from exc
        return value


class ContactMessageOut(Schema):
    message: str


class ContactCsrfOut(Schema):
    message: str
