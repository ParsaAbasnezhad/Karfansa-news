from django.db import models


class NewsSource(models.Model):
    class Category(models.TextChoices):
        ECONOMY = "economy", "اقتصاد"
        BUSINESS = "business", "اقتصاد و کسب‌وکار"
        MARKETS = "markets", "بازارهای مالی"
        INDUSTRY = "industry", "صنعت و تجارت"
        OTHER = "other", "سایر"

    class Health(models.TextChoices):
        UNKNOWN = "unknown", "نامشخص"
        HEALTHY = "healthy", "سالم"
        DEGRADED = "degraded", "دارای خطا"
        UNHEALTHY = "unhealthy", "ناسالم"

    name = models.CharField(max_length=150, verbose_name="نام منبع")

    rss_url = models.URLField(unique=True, verbose_name="آدرس RSS")

    website_url = models.URLField(blank=True, verbose_name="آدرس سایت")

    category = models.CharField(
        max_length=16,
        choices=Category.choices,
        default=Category.OTHER,
        verbose_name="دستهٔ منبع",
    )

    is_active = models.BooleanField(default=True, verbose_name="فعال")

    is_headline_source = models.BooleanField(default=False, verbose_name="منبع تیترهای مهم")

    last_fetched_at = models.DateTimeField(null=True, blank=True, verbose_name="آخرین دریافت")

    last_attempt_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="آخرین تلاش",
    )

    last_fetch_status = models.CharField(
        max_length=16,
        blank=True,
        verbose_name="وضعیت آخرین دریافت",
    )

    last_fetch_error = models.CharField(
        max_length=300,
        blank=True,
        verbose_name="خطای آخرین دریافت",
    )

    last_fetched_count = models.PositiveIntegerField(default=0, verbose_name="تعداد آیتم‌های اخیر")
    last_accepted_count = models.PositiveIntegerField(default=0, verbose_name="پذیرفته‌شدهٔ اخیر")
    last_rejected_count = models.PositiveIntegerField(default=0, verbose_name="ردشدهٔ اخیر")
    last_duplicate_count = models.PositiveIntegerField(default=0, verbose_name="تکراری اخیر")
    last_error_count = models.PositiveIntegerField(default=0, verbose_name="خطای اخیر")
    health_status = models.CharField(
        max_length=16,
        choices=Health.choices,
        default=Health.UNKNOWN,
        verbose_name="سلامت منبع",
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "منبع خبری"
        verbose_name_plural = "منابع خبری"

    def __str__(self):
        return self.name


class NewsFetchRun(models.Model):
    class Status(models.TextChoices):
        RUNNING = "running", "در حال اجرا"
        SUCCESS = "success", "موفق"
        PARTIAL = "partial", "ناقص"
        FAILED = "failed", "ناموفق"
        SKIPPED = "skipped", "ردشده به‌دلیل اجرای هم‌زمان"

    started_at = models.DateTimeField(auto_now_add=True, verbose_name="زمان شروع")
    finished_at = models.DateTimeField(null=True, blank=True, verbose_name="زمان پایان")
    status = models.CharField(
        max_length=16,
        choices=Status.choices,
        default=Status.RUNNING,
        db_index=True,
        verbose_name="وضعیت",
    )
    sources_checked = models.PositiveIntegerField(default=0, verbose_name="منابع بررسی‌شده")
    fetched_count = models.PositiveIntegerField(default=0, verbose_name="دریافت‌شده")
    new_count = models.PositiveIntegerField(default=0, verbose_name="خبر جدید")
    accepted_count = models.PositiveIntegerField(default=0, verbose_name="پذیرفته‌شده")
    rejected_count = models.PositiveIntegerField(default=0, verbose_name="ردشده")
    duplicate_count = models.PositiveIntegerField(default=0, verbose_name="تکراری")
    error_count = models.PositiveIntegerField(default=0, verbose_name="خطا")
    error_summary = models.TextField(blank=True, verbose_name="گزارش خطا")

    class Meta:
        verbose_name = "اجرای دریافت خبر"
        verbose_name_plural = "اجراهای دریافت خبر"
        ordering = ["-started_at"]
        indexes = [models.Index(fields=["-started_at", "status"])]

    def __str__(self):
        return f"RSS {self.started_at:%Y-%m-%d %H:%M} ({self.status})"


class NewsTopic(models.Model):
    name = models.CharField(max_length=100, unique=True, verbose_name="موضوع")

    keywords = models.JSONField(default=list, verbose_name="کلمات کلیدی")

    is_active = models.BooleanField(default=True, verbose_name="فعال")

    position = models.PositiveSmallIntegerField(
        default=0,
        verbose_name="ترتیب نمایش",
    )

    class Meta:
        verbose_name = "موضوع خبری"
        verbose_name_plural = "موضوعات خبری"
        ordering = ["position", "name"]

    def __str__(self):
        return self.name


class News(models.Model):
    source = models.ForeignKey(
        NewsSource, on_delete=models.CASCADE, related_name="news", verbose_name="منبع"
    )

    topic = models.ForeignKey(
        NewsTopic,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="news",
        verbose_name="موضوع",
    )

    title = models.CharField(max_length=300, verbose_name="عنوان")

    summary = models.TextField(blank=True, verbose_name="خلاصه")

    original_url = models.URLField(max_length=1000, unique=True, verbose_name="لینک اصلی")

    image_url = models.URLField(max_length=1000, blank=True, verbose_name="تصویر")

    guid = models.CharField(max_length=1000, blank=True, verbose_name="شناسه RSS")

    published_at = models.DateTimeField(null=True, blank=True, verbose_name="تاریخ انتشار")

    fetched_at = models.DateTimeField(auto_now_add=True, verbose_name="تاریخ دریافت")

    score = models.PositiveSmallIntegerField(default=0, verbose_name="امتیاز ارتباط")

    is_published = models.BooleanField(default=False, verbose_name="منتشر شده")

    is_archived = models.BooleanField(default=False, verbose_name="آرشیو شده")

    is_pinned = models.BooleanField(default=False, verbose_name="خبر ویژه")

    class Meta:
        verbose_name = "خبر"
        verbose_name_plural = "اخبار"
        ordering = ["-published_at"]
        indexes = [
            models.Index(fields=["is_published", "-published_at"]),
            models.Index(fields=["topic", "-published_at"]),
        ]

    def __str__(self):
        return self.title


class NewsIntake(models.Model):
    """One review decision per RSS item, including items that stay unpublished."""

    class Status(models.TextChoices):
        APPROVED = "approved", "تأیید شده"
        REJECTED = "rejected", "رد شده"

    source = models.ForeignKey(
        NewsSource,
        on_delete=models.CASCADE,
        related_name="intakes",
        verbose_name="منبع",
    )

    original_url = models.URLField(
        max_length=1000,
        unique=True,
        verbose_name="لینک اصلی",
    )

    guid = models.CharField(
        max_length=1000,
        blank=True,
        verbose_name="شناسه RSS",
    )

    title = models.CharField(
        max_length=300,
        verbose_name="عنوان",
    )

    status = models.CharField(
        max_length=16,
        choices=Status.choices,
        verbose_name="وضعیت بررسی",
    )

    score = models.PositiveSmallIntegerField(
        default=0,
        verbose_name="امتیاز ارتباط",
    )

    topic_name = models.CharField(
        max_length=100,
        blank=True,
        verbose_name="موضوع",
    )

    decision_reason = models.TextField(blank=True, verbose_name="دلیل تصمیم")

    reviewed_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="زمان بررسی",
    )

    class Meta:
        verbose_name = "بررسی خبر"
        verbose_name_plural = "بررسی اخبار"
        ordering = ["-reviewed_at"]

    def __str__(self):
        return self.title
