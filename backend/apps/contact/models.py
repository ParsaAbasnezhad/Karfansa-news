from django.core.validators import EmailValidator
from django.db import models


class ContactMessage(models.Model):
    name = models.CharField(max_length=120, verbose_name="نام")
    phone = models.CharField(max_length=16, verbose_name="شماره موبایل")
    email = models.EmailField(validators=[EmailValidator()], verbose_name="ایمیل")
    subject = models.CharField(max_length=120, verbose_name="موضوع")
    message = models.TextField(max_length=3000, verbose_name="پیام")
    is_read = models.BooleanField(default=False, verbose_name="خوانده‌شده")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاریخ دریافت")

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "پیام تماس"
        verbose_name_plural = "پیام‌های تماس"

    def __str__(self) -> str:
        return f"{self.subject} — {self.name}"
