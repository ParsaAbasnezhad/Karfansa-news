"""Editorial workflow for staff writers and publishing editors."""

from django import forms
from django.conf import settings
from django.contrib import admin, messages
from django.core.exceptions import PermissionDenied, ValidationError
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, render
from django.urls import path, reverse
from django.utils import timezone
from django.utils.html import format_html

from .models import EditorialArticle, EditorialCategory, EditorialImage, EditorialTag
from .sanitizer import sanitize_article_html

PUBLISH_PERMISSION = "editorial.publish_editorialarticle"


class RichTextWidget(forms.Textarea):
    def __init__(self, attrs=None) -> None:
        super().__init__({"data-editorial-richtext": "true", "rows": 18, **(attrs or {})})

    def render(self, name, value, attrs=None, renderer=None):
        return super().render(name, sanitize_article_html(value or ""), attrs, renderer)

    class Media:
        js = ("editorial/editor.js",)
        css = {"all": ("editorial/editor.css",)}


class EditorialArticleForm(forms.ModelForm):
    class Meta:
        model = EditorialArticle
        fields = (
            "title",
            "slug",
            "summary",
            "content",
            "featured_image",
            "category",
            "tags",
            "author",
            "editor",
            "source_name",
            "source_url",
            "status",
            "published_at",
            "is_featured",
            "is_breaking",
            "is_pinned",
            "priority",
            "seo_title",
            "seo_description",
            "seo_social_image",
            "seo_noindex",
            "seo_canonical_url",
        )
        widgets = {"content": RichTextWidget()}


def _seo_snippet_preview(
    obj: EditorialArticle | EditorialCategory | None, *, category: bool = False
) -> str:
    site = getattr(settings, "SEO_SITE_URL", "https://karfansa.news.ir").rstrip("/")
    path = "/editorial/category/" if category else "/editorial/"
    fallback = obj.name if isinstance(obj, EditorialCategory) else obj.title if obj else ""
    description = (
        obj.seo_description or (obj.summary if isinstance(obj, EditorialArticle) else "")
        if obj
        else ""
    )
    url = (obj.seo_canonical_url if obj else "") or f"{site}{path}{obj.slug if obj else ''}"
    return format_html(
        '<div class="editorial-seo-preview" data-seo-kind="{}" data-seo-site="{}">'
        '<span class="editorial-seo-preview__url">{}</span>'
        '<strong class="editorial-seo-preview__title">{}</strong>'
        '<span class="editorial-seo-preview__description">{}</span>'
        "<small>نمونه تقریبی نمایش در جستجو؛ گوگل ممکن است متن دیگری انتخاب کند.</small>"
        "</div>",
        "category" if category else "article",
        site,
        url,
        (obj.seo_title if obj else "") or fallback,
        description,
    )


class EditorialImageInline(admin.TabularInline):
    model = EditorialImage
    extra = 0
    fields = ("image", "alt_text", "caption", "position", "thumbnail")
    readonly_fields = ("thumbnail",)

    @admin.display(description="نمایش")
    def thumbnail(self, obj: EditorialImage) -> str:
        if not obj.image:
            return "—"
        return format_html(
            '<img src="{}" alt="" style="width:80px;height:56px;object-fit:cover">', obj.image.url
        )


@admin.register(EditorialCategory)
class EditorialCategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "position", "is_active", "seo_noindex")
    list_filter = ("is_active", "seo_noindex")
    list_editable = ("position", "is_active")
    search_fields = ("name", "slug")
    ordering = ("position", "name")
    readonly_fields = ("seo_snippet_preview",)
    fieldsets = (
        ("دسته", {"fields": ("name", "slug", "position", "is_active")}),
        (
            "سئو",
            {
                "fields": (
                    "seo_title",
                    "seo_description",
                    "seo_social_image",
                    "seo_noindex",
                    "seo_canonical_url",
                    "seo_snippet_preview",
                )
            },
        ),
    )

    class Media:
        js = ("editorial/seo-admin.js",)
        css = {"all": ("editorial/seo-admin.css",)}

    @admin.display(description="پیش‌نمایش نتیجه جستجو")
    def seo_snippet_preview(self, obj: EditorialCategory | None) -> str:
        return _seo_snippet_preview(obj, category=True)


@admin.register(EditorialTag)
class EditorialTagAdmin(admin.ModelAdmin):
    list_display = ("name", "slug")
    search_fields = ("name", "slug")


@admin.action(description="ارسال خبرهای انتخاب‌شده برای بررسی")
def submit_for_review(modeladmin, request, queryset) -> None:
    count = queryset.filter(status=EditorialArticle.Status.DRAFT).update(
        status=EditorialArticle.Status.PENDING_REVIEW, updated_at=timezone.now()
    )
    modeladmin.message_user(request, f"{count} خبر برای بررسی فرستاده شد.", messages.SUCCESS)


@admin.action(description="انتشار خبرهای انتخاب‌شده")
def publish_articles(modeladmin, request, queryset) -> None:
    if not request.user.has_perm(PUBLISH_PERMISSION):
        raise PermissionDenied
    count = 0
    for article in queryset:
        if not article.title.strip() or not article.content.strip() or not article.summary.strip():
            continue
        article.status = EditorialArticle.Status.PUBLISHED
        if article.published_at is None:
            article.published_at = timezone.now()
        article.save()
        count += 1
    modeladmin.message_user(request, f"{count} خبر منتشر شد.", messages.SUCCESS)


@admin.action(description="بایگانی خبرهای انتخاب‌شده")
def archive_articles(modeladmin, request, queryset) -> None:
    if not request.user.has_perm(PUBLISH_PERMISSION):
        raise PermissionDenied
    count = queryset.update(status=EditorialArticle.Status.ARCHIVED, updated_at=timezone.now())
    if count:
        from .sitemap import invalidate_sitemaps

        invalidate_sitemaps()
    modeladmin.message_user(request, f"{count} خبر بایگانی شد.", messages.SUCCESS)


@admin.action(description="ویژه‌کردن خبرهای انتخاب‌شده")
def feature_articles(modeladmin, request, queryset) -> None:
    if not request.user.has_perm(PUBLISH_PERMISSION):
        raise PermissionDenied
    count = queryset.update(is_featured=True, updated_at=timezone.now())
    modeladmin.message_user(request, f"{count} خبر ویژه شد.", messages.SUCCESS)


@admin.action(description="سنجاق‌کردن خبرهای انتخاب‌شده")
def pin_articles(modeladmin, request, queryset) -> None:
    if not request.user.has_perm(PUBLISH_PERMISSION):
        raise PermissionDenied
    count = queryset.update(is_pinned=True, updated_at=timezone.now())
    modeladmin.message_user(request, f"{count} خبر سنجاق شد.", messages.SUCCESS)


@admin.register(EditorialArticle)
class EditorialArticleAdmin(admin.ModelAdmin):
    form = EditorialArticleForm
    inlines = (EditorialImageInline,)
    list_display = (
        "thumbnail",
        "title",
        "category",
        "author",
        "status",
        "is_featured",
        "is_breaking",
        "is_pinned",
        "priority",
        "published_at",
        "view_count",
    )
    list_filter = ("status", "category", "is_featured", "is_breaking", "is_pinned", "published_at")
    search_fields = ("title", "summary", "content", "slug", "source_name")
    autocomplete_fields = ("category", "tags", "author", "editor")
    list_select_related = ("category", "author")
    ordering = ("-is_pinned", "-priority", "-published_at", "-id")
    list_per_page = 30
    save_on_top = True
    actions = (
        submit_for_review,
        publish_articles,
        archive_articles,
        feature_articles,
        pin_articles,
    )
    readonly_fields = (
        "thumbnail",
        "preview_link",
        "reading_time",
        "view_count",
        "created_at",
        "updated_at",
        "seo_snippet_preview",
    )
    fieldsets = (
        (
            "خبر",
            {
                "fields": (
                    "title",
                    "slug",
                    "summary",
                    "content",
                    "featured_image",
                    "thumbnail",
                    "category",
                    "tags",
                )
            },
        ),
        ("تحریریه", {"fields": ("author", "editor", "source_name", "source_url")}),
        (
            "انتشار",
            {
                "fields": (
                    "status",
                    "published_at",
                    "is_featured",
                    "is_breaking",
                    "is_pinned",
                    "priority",
                    "preview_link",
                )
            },
        ),
        (
            "سئو",
            {
                "fields": (
                    "seo_title",
                    "seo_description",
                    "seo_social_image",
                    "seo_noindex",
                    "seo_canonical_url",
                    "seo_snippet_preview",
                )
            },
        ),
        (
            "آمار",
            {
                "fields": ("reading_time", "view_count", "created_at", "updated_at"),
                "classes": ("collapse",),
            },
        ),
    )

    class Media:
        js = ("editorial/seo-admin.js",)
        css = {"all": ("editorial/seo-admin.css",)}

    @admin.display(description="پیش‌نمایش نتیجه جستجو")
    def seo_snippet_preview(self, obj: EditorialArticle | None) -> str:
        return _seo_snippet_preview(obj)

    def has_change_permission(self, request, obj=None):
        if (
            obj is not None
            and obj.status
            in {
                EditorialArticle.Status.PUBLISHED,
                EditorialArticle.Status.ARCHIVED,
            }
            and not request.user.has_perm(PUBLISH_PERMISSION)
        ):
            return False
        return super().has_change_permission(request, obj)

    def get_urls(self):
        custom = [
            path(
                "<path:object_id>/preview/",
                self.admin_site.admin_view(self.preview_view),
                name="editorial_editorialarticle_preview",
            )
        ]
        return custom + super().get_urls()

    def preview_view(self, request: HttpRequest, object_id: str) -> HttpResponse:
        if not self.has_view_permission(request):
            raise PermissionDenied
        article = get_object_or_404(
            EditorialArticle.objects.select_related("author", "category").prefetch_related(
                "gallery"
            ),
            pk=object_id,
        )
        return render(
            request,
            "editorial/admin_preview.html",
            {
                "article": article,
                "safe_content": sanitize_article_html(article.content),
                "title": "پیش‌نمایش خبر",
            },
        )

    def get_form(self, request, obj=None, **kwargs):
        base_form = super().get_form(request, obj, **kwargs)
        can_publish = request.user.has_perm(PUBLISH_PERMISSION)
        initial_status = obj.status if obj else EditorialArticle.Status.DRAFT

        class PermissionCheckedForm(base_form):
            def clean_status(self):
                status = self.cleaned_data["status"]
                protected = {EditorialArticle.Status.PUBLISHED, EditorialArticle.Status.ARCHIVED}
                if (
                    not can_publish
                    and status != initial_status
                    and (status in protected or initial_status in protected)
                ):
                    raise ValidationError("برای انتشار یا بایگانی خبر مجوز لازم است.")
                return status

        return PermissionCheckedForm

    def save_model(self, request, obj, form, change):
        old_status = (
            EditorialArticle.objects.filter(pk=obj.pk).values_list("status", flat=True).first()
            if change
            else None
        )
        protected = {EditorialArticle.Status.PUBLISHED, EditorialArticle.Status.ARCHIVED}
        if (
            not request.user.has_perm(PUBLISH_PERMISSION)
            and obj.status != old_status
            and (obj.status in protected or old_status in protected)
        ):
            raise PermissionDenied
        if obj.author_id is None:
            obj.author = request.user
        if (
            request.user.has_perm(PUBLISH_PERMISSION)
            and obj.status == EditorialArticle.Status.PUBLISHED
        ):
            obj.editor = request.user
        super().save_model(request, obj, form, change)

    def get_readonly_fields(self, request, obj=None):
        fields = list(super().get_readonly_fields(request, obj))
        if not request.user.has_perm(PUBLISH_PERMISSION):
            fields.extend(("is_featured", "is_breaking", "is_pinned", "priority", "published_at"))
        return fields

    def get_actions(self, request):
        actions = super().get_actions(request)
        if not request.user.has_perm(PUBLISH_PERMISSION):
            for name in (
                "publish_articles",
                "archive_articles",
                "feature_articles",
                "pin_articles",
            ):
                actions.pop(name, None)
        return actions

    @admin.display(description="تصویر")
    def thumbnail(self, obj: EditorialArticle) -> str:
        if not obj.featured_image:
            return "—"
        return format_html(
            '<img src="{}" alt="" style="width:76px;height:52px;'
            'object-fit:cover;border-radius:4px">',
            obj.featured_image.url,
        )

    @admin.display(description="پیش‌نمایش")
    def preview_link(self, obj: EditorialArticle) -> str:
        if not obj.pk:
            return "ابتدا پیش‌نویس را ذخیره کنید."
        url = reverse("admin:editorial_editorialarticle_preview", args=[obj.pk])
        return format_html('<a href="{}" target="_blank" rel="noopener">نمایش پیش‌نمایش</a>', url)
