from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone

from apps.advertising.validators import validate_safe_destination_url
from apps.common.models import TimeStampedModel


class AdvertisementSlide(TimeStampedModel):
    title = models.CharField(max_length=160, verbose_name="عنوان")
    subtitle = models.CharField(max_length=160, blank=True, verbose_name="زیرعنوان")
    description = models.TextField(max_length=600, blank=True, verbose_name="توضیحات")
    image_desktop = models.ImageField(
        upload_to="advertising/slides/desktop/%Y/%m/",
        verbose_name="تصویر دسکتاپ",
    )
    image_mobile = models.ImageField(
        upload_to="advertising/slides/mobile/%Y/%m/",
        blank=True,
        verbose_name="تصویر موبایل",
    )
    button_text = models.CharField(max_length=80, blank=True, verbose_name="متن دکمه")
    button_url = models.CharField(
        max_length=500,
        blank=True,
        validators=[validate_safe_destination_url],
        verbose_name="لینک دکمه",
        help_text="مسیر داخلی مانند /news یا پیوند امن http(s).",
    )
    sort_order = models.PositiveIntegerField(default=0, verbose_name="ترتیب نمایش")
    is_active = models.BooleanField(default=True, verbose_name="فعال")
    starts_at = models.DateTimeField(null=True, blank=True, verbose_name="شروع نمایش")
    ends_at = models.DateTimeField(null=True, blank=True, verbose_name="پایان نمایش")

    class Meta:
        ordering = ["sort_order", "-updated_at"]
        verbose_name = "اسلاید تبلیغاتی"
        verbose_name_plural = "اسلایدهای تبلیغاتی"
        indexes = [
            models.Index(fields=["is_active", "sort_order"]),
            models.Index(fields=["starts_at", "ends_at"]),
        ]

    def __str__(self) -> str:
        return self.title

    def clean(self) -> None:
        super().clean()
        if self.button_url:
            validate_safe_destination_url(self.button_url)
        if self.starts_at and self.ends_at and self.starts_at >= self.ends_at:
            raise ValidationError({"ends_at": "زمان پایان باید بعد از زمان شروع باشد."})

    def is_currently_visible(self, now=None) -> bool:
        moment = now or timezone.now()
        if not self.is_active:
            return False
        if self.starts_at and self.starts_at > moment:
            return False
        if self.ends_at and self.ends_at < moment:
            return False
        return True
