import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="ContactMessage",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("name", models.CharField(max_length=120, verbose_name="نام")),
                (
                    "email",
                    models.EmailField(
                        max_length=254,
                        validators=[django.core.validators.EmailValidator()],
                        verbose_name="ایمیل",
                    ),
                ),
                ("subject", models.CharField(max_length=120, verbose_name="موضوع")),
                ("message", models.TextField(max_length=3000, verbose_name="پیام")),
                ("is_read", models.BooleanField(default=False, verbose_name="خوانده‌شده")),
                (
                    "created_at",
                    models.DateTimeField(auto_now_add=True, verbose_name="تاریخ دریافت"),
                ),
            ],
            options={
                "verbose_name": "پیام تماس",
                "verbose_name_plural": "پیام‌های تماس",
                "ordering": ["-created_at"],
            },
        ),
    ]
