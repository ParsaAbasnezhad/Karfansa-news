# ruff: noqa: RUF001 - Persian field labels intentionally contain Arabic-script confusables.
from django.core.exceptions import ValidationError
from django.db import models

from apps.advertising.validators import validate_safe_destination_url
from apps.common.image_validation import validate_staff_image
from apps.common.models import TimeStampedModel


class SingletonModel(models.Model):
    """Ensure only one editable row exists for site-wide pages."""

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValidationError("این صفحه قابل حذف نیست.")

    @classmethod
    def load(cls):
        obj, _created = cls.objects.get_or_create(pk=1)
        return obj


class AboutPage(SingletonModel, TimeStampedModel):
    hero_kicker = models.CharField(max_length=120, blank=True, verbose_name="عنوان کوتاه هیرو")
    title = models.CharField(max_length=200, verbose_name="عنوان اصلی")
    subtitle = models.CharField(max_length=240, blank=True, verbose_name="زیرعنوان")
    intro = models.TextField(verbose_name="متن معرفی")
    hero_image = models.ImageField(
        upload_to="pages/about/hero/%Y/%m/",
        validators=[validate_staff_image],
        blank=True,
        verbose_name="تصویر اصلی",
    )
    mission_title = models.CharField(max_length=160, blank=True, verbose_name="عنوان مأموریت")
    mission = models.TextField(blank=True, verbose_name="مأموریت مجموعه")
    vision_title = models.CharField(max_length=160, blank=True, verbose_name="عنوان چشم‌انداز")
    vision = models.TextField(blank=True, verbose_name="چشم‌انداز مجموعه")
    values_title = models.CharField(max_length=160, blank=True, verbose_name="عنوان ارزش‌ها")
    values = models.TextField(blank=True, verbose_name="ارزش‌های سازمانی")
    goals_title = models.CharField(max_length=160, blank=True, verbose_name="عنوان اهداف")
    goals = models.TextField(blank=True, verbose_name="اهداف پلتفرم")
    mission_image = models.ImageField(
        upload_to="pages/about/mission/%Y/%m/",
        validators=[validate_staff_image],
        blank=True,
        verbose_name="تصویر بخش مأموریت",
    )
    story_eyebrow = models.CharField(max_length=120, blank=True, verbose_name="برچسب روش کار")
    story_title = models.CharField(max_length=200, blank=True, verbose_name="عنوان روش کار")
    story_body = models.TextField(blank=True, verbose_name="متن روش کار")
    cta_eyebrow = models.CharField(max_length=120, blank=True, verbose_name="برچسب بخش پایانی")
    cta_title = models.CharField(max_length=200, blank=True, verbose_name="عنوان بخش پایانی")
    closing_text = models.TextField(blank=True, verbose_name="متن بخش پایانی")
    primary_cta_label = models.CharField(max_length=80, blank=True, verbose_name="متن دکمه اصلی")
    primary_cta_url = models.CharField(
        max_length=500,
        blank=True,
        validators=[validate_safe_destination_url],
        verbose_name="لینک دکمه اصلی",
    )
    secondary_cta_label = models.CharField(max_length=80, blank=True, verbose_name="متن دکمه فرعی")
    secondary_cta_url = models.CharField(
        max_length=500,
        blank=True,
        validators=[validate_safe_destination_url],
        verbose_name="لینک دکمه فرعی",
    )
    show_globe = models.BooleanField(default=True, verbose_name="نمایش کره سه‌بعدی")
    seo_title = models.CharField(max_length=180, blank=True, verbose_name="عنوان SEO")
    seo_description = models.CharField(max_length=320, blank=True, verbose_name="توضیح SEO")

    class Meta:
        verbose_name = "صفحه درباره ما"
        verbose_name_plural = "صفحه درباره ما"

    def __str__(self) -> str:
        return self.title or "درباره ما"


class AboutFeature(TimeStampedModel):
    class Kind(models.TextChoices):
        PURPOSE = "purpose", "تعهد صفحه"
        PRINCIPLE = "principle", "اصل"
        VALUE = "value", "ارزش"
        OTHER = "other", "سایر"

    page = models.ForeignKey(
        AboutPage,
        on_delete=models.CASCADE,
        related_name="features",
        verbose_name="صفحه",
    )
    kind = models.CharField(
        max_length=20,
        choices=Kind.choices,
        default=Kind.PURPOSE,
        verbose_name="نوع",
    )
    label = models.CharField(max_length=80, blank=True, verbose_name="برچسب")
    title = models.CharField(max_length=180, verbose_name="عنوان")
    body = models.TextField(verbose_name="متن")
    sort_order = models.PositiveIntegerField(default=0, verbose_name="ترتیب")
    is_active = models.BooleanField(default=True, verbose_name="فعال")

    class Meta:
        ordering = ["sort_order", "id"]
        verbose_name = "ویژگی درباره ما"
        verbose_name_plural = "ویژگی‌های درباره ما"

    def __str__(self) -> str:
        return self.title


class AboutStatistic(TimeStampedModel):
    page = models.ForeignKey(
        AboutPage,
        on_delete=models.CASCADE,
        related_name="statistics",
        verbose_name="صفحه",
    )
    label = models.CharField(max_length=120, verbose_name="برچسب")
    value = models.CharField(max_length=40, verbose_name="مقدار")
    sort_order = models.PositiveIntegerField(default=0, verbose_name="ترتیب")
    is_active = models.BooleanField(default=True, verbose_name="فعال")

    class Meta:
        ordering = ["sort_order", "id"]
        verbose_name = "آمار درباره ما"
        verbose_name_plural = "آمارهای درباره ما"

    def __str__(self) -> str:
        return f"{self.label}: {self.value}"


class AboutTeamMember(TimeStampedModel):
    page = models.ForeignKey(
        AboutPage,
        on_delete=models.CASCADE,
        related_name="team_members",
        verbose_name="صفحه",
    )
    name = models.CharField(max_length=120, verbose_name="نام")
    role = models.CharField(max_length=160, blank=True, verbose_name="سمت")
    bio = models.TextField(blank=True, verbose_name="بیوگرافی")
    photo = models.ImageField(
        upload_to="pages/about/team/%Y/%m/",
        validators=[validate_staff_image],
        blank=True,
        verbose_name="تصویر",
    )
    sort_order = models.PositiveIntegerField(default=0, verbose_name="ترتیب")
    is_active = models.BooleanField(default=True, verbose_name="فعال")

    class Meta:
        ordering = ["sort_order", "id"]
        verbose_name = "عضو تیم"
        verbose_name_plural = "اعضای تیم"

    def __str__(self) -> str:
        return self.name


class ContactPage(SingletonModel, TimeStampedModel):
    title = models.CharField(max_length=200, verbose_name="عنوان صفحه")
    description = models.TextField(blank=True, verbose_name="توضیحات")
    support_email = models.EmailField(blank=True, verbose_name="ایمیل پشتیبانی")
    business_email = models.EmailField(blank=True, verbose_name="ایمیل تجاری")
    phone = models.CharField(max_length=40, blank=True, verbose_name="شماره تماس")
    whatsapp = models.CharField(max_length=40, blank=True, verbose_name="شماره واتساپ")
    office_address = models.TextField(blank=True, verbose_name="آدرس دفتر")
    response_hours = models.CharField(max_length=200, blank=True, verbose_name="ساعات پاسخ‌گویی")
    map_url = models.CharField(
        max_length=500,
        blank=True,
        validators=[validate_safe_destination_url],
        verbose_name="لینک نقشه",
    )
    instagram_url = models.CharField(
        max_length=500,
        blank=True,
        validators=[validate_safe_destination_url],
        verbose_name="اینستاگرام",
    )
    linkedin_url = models.CharField(
        max_length=500,
        blank=True,
        validators=[validate_safe_destination_url],
        verbose_name="لینکدین",
    )
    telegram_url = models.CharField(
        max_length=500,
        blank=True,
        validators=[validate_safe_destination_url],
        verbose_name="تلگرام",
    )
    support_text = models.TextField(blank=True, verbose_name="متن بخش پشتیبانی")
    form_intro = models.CharField(max_length=240, blank=True, verbose_name="معرفی فرم")
    seo_title = models.CharField(max_length=180, blank=True, verbose_name="عنوان SEO")
    seo_description = models.CharField(max_length=320, blank=True, verbose_name="توضیح SEO")

    class Meta:
        verbose_name = "صفحه تماس با ما"
        verbose_name_plural = "صفحه تماس با ما"

    def __str__(self) -> str:
        return self.title or "تماس با ما"


class ContactFAQ(TimeStampedModel):
    page = models.ForeignKey(
        ContactPage,
        on_delete=models.CASCADE,
        related_name="faqs",
        verbose_name="صفحه",
    )
    question = models.CharField(max_length=240, verbose_name="سؤال")
    answer = models.TextField(verbose_name="پاسخ")
    sort_order = models.PositiveIntegerField(default=0, verbose_name="ترتیب")
    is_active = models.BooleanField(default=True, verbose_name="فعال")

    class Meta:
        ordering = ["sort_order", "id"]
        verbose_name = "پرسش متداول تماس"
        verbose_name_plural = "پرسش‌های متداول تماس"

    def __str__(self) -> str:
        return self.question
