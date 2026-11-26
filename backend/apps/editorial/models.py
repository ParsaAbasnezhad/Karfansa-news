"""Human-edited news, kept separate from RSS intake and its lifecycle."""

import math
import re
import uuid
from pathlib import Path

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import URLValidator
from django.db import models
from django.utils import timezone
from django.utils.html import strip_tags
from django.utils.text import slugify

from apps.common.image_validation import validate_staff_image

from .images import create_webp_variants
from .sanitizer import sanitize_article_html
from .seo import canonical_path, validate_article_canonical_url, validate_category_canonical_url


def _unique_slug(instance: models.Model, text: str, *, max_length: int = 240) -> str:
    base = slugify(text, allow_unicode=True)[:max_length].strip("-") or "article"
    slug = base
    suffix = 2
    manager = type(instance)._default_manager
    while manager.filter(slug=slug).exclude(pk=instance.pk).exists():
        tail = f"-{suffix}"
        slug = f"{base[: max_length - len(tail)]}{tail}"
        suffix += 1
    return slug


def _image_path(folder: str, filename: str) -> str:
    extension = Path(filename).suffix.lower()
    if extension not in {".jpg", ".jpeg", ".png", ".webp", ".gif", ".avif"}:
        extension = ".jpg"
    return f"editorial/{folder}/{timezone.now():%Y/%m}/{uuid.uuid4().hex}{extension}"


def featured_image_path(instance: models.Model, filename: str) -> str:
    return _image_path("featured", filename)


def gallery_image_path(instance: models.Model, filename: str) -> str:
    return _image_path("gallery", filename)


def social_image_path(instance: models.Model, filename: str) -> str:
    return _image_path("social", filename)


class EditorialCategory(models.Model):
    name = models.CharField(max_length=100, unique=True, verbose_name="نام")
    slug = models.SlugField(
        max_length=120, allow_unicode=True, unique=True, blank=True, verbose_name="آدرس"
    )
    position = models.PositiveSmallIntegerField(default=0, verbose_name="ترتیب")
    is_active = models.BooleanField(default=True, verbose_name="فعال")
    seo_title = models.CharField(max_length=160, blank=True, verbose_name="عنوان سئو")
    seo_description = models.CharField(max_length=300, blank=True, verbose_name="توضیح سئو")
    seo_social_image = models.ImageField(
        upload_to=social_image_path,
        validators=[validate_staff_image],
        blank=True,
        verbose_name="تصویر اشتراک‌گذاری",
    )
    seo_noindex = models.BooleanField(default=False, verbose_name="عدم نمایش در جستجو")
    seo_canonical_url = models.URLField(
        max_length=500,
        blank=True,
        validators=[validate_category_canonical_url],
        verbose_name="آدرس کنونیکال جایگزین",
    )

    class Meta:
        ordering = ["position", "name"]
        verbose_name = "دسته‌بندی اختصاصی"
        verbose_name_plural = "دسته‌بندی‌های اختصاصی"

    def __str__(self) -> str:
        return self.name

    def save(self, *args, **kwargs) -> None:
        if not self.slug:
            self.slug = _unique_slug(self, self.name, max_length=120)
        self._validate_canonical_target()
        super().save(*args, **kwargs)

    def _validate_canonical_target(self) -> None:
        if self.seo_canonical_url:
            target_slug = canonical_path(self.seo_canonical_url, kind="category")
            if target_slug == self.slug:
                self.seo_canonical_url = ""
                return
            if (
                target_slug != self.slug
                and not type(self)
                .objects.filter(
                    slug=target_slug,
                    is_active=True,
                    seo_noindex=False,
                    seo_canonical_url="",
                    articles__status=EditorialArticle.Status.PUBLISHED,
                    articles__published_at__lte=timezone.now(),
                )
                .exists()
            ):
                raise ValidationError(
                    {"seo_canonical_url": "دسته مقصد باید محتوای منتشرشده داشته باشد."}
                )

    def clean(self) -> None:
        super().clean()
        self._validate_canonical_target()


class EditorialTag(models.Model):
    name = models.CharField(max_length=80, unique=True, verbose_name="نام")
    slug = models.SlugField(
        max_length=100, allow_unicode=True, unique=True, blank=True, verbose_name="آدرس"
    )

    class Meta:
        ordering = ["name"]
        verbose_name = "برچسب اختصاصی"
        verbose_name_plural = "برچسب‌های اختصاصی"

    def __str__(self) -> str:
        return self.name

    def save(self, *args, **kwargs) -> None:
        if not self.slug:
            self.slug = _unique_slug(self, self.name, max_length=100)
        super().save(*args, **kwargs)


class EditorialArticle(models.Model):
    class Status(models.TextChoices):
        DRAFT = "draft", "پیش‌نویس"
        PENDING_REVIEW = "pending_review", "در انتظار بررسی"
        PUBLISHED = "published", "منتشرشده"
        ARCHIVED = "archived", "بایگانی‌شده"

    title = models.CharField(max_length=300, verbose_name="عنوان")
    slug = models.SlugField(
        max_length=240, allow_unicode=True, unique=True, blank=True, verbose_name="آدرس یکتا"
    )
    summary = models.TextField(max_length=1000, verbose_name="خلاصه")
    content = models.TextField(verbose_name="متن خبر")
    featured_image = models.ImageField(
        upload_to=featured_image_path,
        validators=[validate_staff_image],
        blank=True,
        width_field="featured_image_width",
        height_field="featured_image_height",
        verbose_name="تصویر اصلی",
    )
    featured_image_width = models.PositiveIntegerField(null=True, blank=True, editable=False)
    featured_image_height = models.PositiveIntegerField(null=True, blank=True, editable=False)
    featured_image_variants = models.JSONField(default=dict, editable=False)
    category = models.ForeignKey(
        EditorialCategory,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="articles",
        verbose_name="دسته‌بندی",
    )
    tags = models.ManyToManyField(
        EditorialTag, blank=True, related_name="articles", verbose_name="برچسب"
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="editorial_articles_authored",
        verbose_name="نویسنده",
    )
    editor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="editorial_articles_edited",
        verbose_name="ویراستار",
    )
    source_name = models.CharField(max_length=200, blank=True, verbose_name="نام منبع")
    source_url = models.URLField(max_length=1000, blank=True, verbose_name="لینک منبع")
    published_at = models.DateTimeField(
        null=True, blank=True, db_index=True, verbose_name="زمان انتشار"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="زمان ثبت")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="آخرین ویرایش")
    reading_time = models.PositiveSmallIntegerField(
        default=1, editable=False, verbose_name="زمان مطالعه (دقیقه)"
    )
    view_count = models.PositiveIntegerField(default=0, editable=False, verbose_name="بازدید")
    is_featured = models.BooleanField(default=False, verbose_name="ویژه")
    is_breaking = models.BooleanField(default=False, verbose_name="فوری")
    is_pinned = models.BooleanField(default=False, verbose_name="سنجاق‌شده")
    priority = models.PositiveSmallIntegerField(default=0, verbose_name="اولویت")
    status = models.CharField(
        max_length=16,
        choices=Status.choices,
        default=Status.DRAFT,
        db_index=True,
        verbose_name="وضعیت",
    )
    seo_title = models.CharField(max_length=160, blank=True, verbose_name="عنوان سئو")
    seo_description = models.CharField(max_length=300, blank=True, verbose_name="توضیح سئو")
    seo_social_image = models.ImageField(
        upload_to=social_image_path,
        validators=[validate_staff_image],
        blank=True,
        verbose_name="تصویر اشتراک‌گذاری",
    )
    seo_noindex = models.BooleanField(default=False, verbose_name="عدم نمایش در جستجو")
    seo_canonical_url = models.URLField(
        max_length=500,
        blank=True,
        validators=[validate_article_canonical_url],
        verbose_name="آدرس کنونیکال جایگزین",
    )

    class Meta:
        ordering = ["-is_pinned", "-priority", "-published_at", "-id"]
        verbose_name = "خبر اختصاصی"
        verbose_name_plural = "اخبار اختصاصی"
        permissions = [
            ("publish_editorialarticle", "Can approve, publish and archive editorial articles")
        ]
        indexes = [
            models.Index(fields=["status", "-is_pinned", "-priority", "-published_at"]),
            models.Index(fields=["status", "-published_at"]),
        ]

    def __str__(self) -> str:
        return self.title

    def save(self, *args, **kwargs) -> None:
        previous_image = (
            type(self).objects.filter(pk=self.pk).values_list("featured_image", flat=True).first()
            if self.pk
            else None
        )
        if not self.slug:
            self.slug = _unique_slug(self, self.title)
        self._validate_canonical_target()
        if self.source_url:
            try:
                URLValidator(schemes=["http", "https"])(self.source_url)
            except ValidationError as exc:
                raise ValidationError(
                    {"source_url": "لینک منبع باید آدرس معتبر http یا https باشد."}
                ) from exc
        self.content = sanitize_article_html(self.content)
        words = re.findall(r"\w+", strip_tags(self.content), flags=re.UNICODE)
        self.reading_time = max(1, math.ceil(len(words) / 200))
        if self.status == self.Status.PUBLISHED and self.published_at is None:
            self.published_at = timezone.now()
        super().save(*args, **kwargs)
        if self.featured_image and (
            previous_image != self.featured_image.name or not self.featured_image_variants
        ):
            self.featured_image_variants = create_webp_variants(self.featured_image)
            type(self).objects.filter(pk=self.pk).update(
                featured_image_variants=self.featured_image_variants
            )
        elif not self.featured_image and self.featured_image_variants:
            self.featured_image_variants = {}
            type(self).objects.filter(pk=self.pk).update(featured_image_variants={})

    def _validate_canonical_target(self) -> None:
        if self.seo_canonical_url:
            target_slug = canonical_path(self.seo_canonical_url, kind="article")
            if target_slug == self.slug:
                self.seo_canonical_url = ""
                return
            if (
                target_slug != self.slug
                and not type(self)
                .objects.filter(
                    slug=target_slug,
                    status=self.Status.PUBLISHED,
                    seo_noindex=False,
                    seo_canonical_url="",
                    published_at__lte=timezone.now(),
                )
                .exists()
            ):
                raise ValidationError({"seo_canonical_url": "خبر مقصد باید منتشرشده و موجود باشد."})

    def clean(self) -> None:
        super().clean()
        self._validate_canonical_target()


class EditorialImage(models.Model):
    article = models.ForeignKey(
        EditorialArticle,
        on_delete=models.CASCADE,
        related_name="gallery",
        verbose_name="خبر",
    )
    image = models.ImageField(
        upload_to=gallery_image_path,
        validators=[validate_staff_image],
        width_field="width",
        height_field="height",
        verbose_name="تصویر",
    )
    width = models.PositiveIntegerField(null=True, blank=True, editable=False)
    height = models.PositiveIntegerField(null=True, blank=True, editable=False)
    variants = models.JSONField(default=dict, editable=False)
    alt_text = models.CharField(max_length=200, blank=True, verbose_name="متن جایگزین")
    caption = models.CharField(max_length=300, blank=True, verbose_name="توضیح تصویر")
    position = models.PositiveSmallIntegerField(default=0, verbose_name="ترتیب")

    class Meta:
        ordering = ["position", "id"]
        verbose_name = "تصویر تکمیلی"
        verbose_name_plural = "تصاویر تکمیلی"

    def __str__(self) -> str:
        return self.caption or f"تصویر {self.pk}"

    def save(self, *args, **kwargs) -> None:
        previous_image = (
            type(self).objects.filter(pk=self.pk).values_list("image", flat=True).first()
            if self.pk
            else None
        )
        super().save(*args, **kwargs)
        if self.image and (previous_image != self.image.name or not self.variants):
            self.variants = create_webp_variants(self.image)
            type(self).objects.filter(pk=self.pk).update(variants=self.variants)
