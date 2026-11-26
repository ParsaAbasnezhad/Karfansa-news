from django.contrib import admin, messages

from .models import News, NewsFetchRun, NewsIntake, NewsSource, NewsTopic


@admin.action(description="فعال‌کردن منابع انتخاب‌شده")
def activate_sources(modeladmin, request, queryset):
    updated = queryset.update(is_active=True)
    modeladmin.message_user(request, f"{updated} منبع فعال شد.", messages.SUCCESS)


@admin.action(description="غیرفعال‌کردن منابع انتخاب‌شده")
def deactivate_sources(modeladmin, request, queryset):
    updated = queryset.update(is_active=False)
    modeladmin.message_user(request, f"{updated} منبع غیرفعال شد.", messages.SUCCESS)


@admin.action(description="انتشار خبرهای انتخاب‌شده")
def publish_news(modeladmin, request, queryset):
    updated = queryset.update(is_published=True, is_archived=False)
    if updated:
        from apps.editorial.sitemap import invalidate_sitemaps

        invalidate_sitemaps()
    modeladmin.message_user(request, f"{updated} خبر منتشر شد.", messages.SUCCESS)


@admin.action(description="بایگانی خبرهای انتخاب‌شده")
def archive_news(modeladmin, request, queryset):
    updated = queryset.update(is_archived=True, is_published=False)
    if updated:
        from apps.editorial.sitemap import invalidate_sitemaps

        invalidate_sitemaps()
    modeladmin.message_user(request, f"{updated} خبر بایگانی شد.", messages.SUCCESS)


@admin.register(NewsSource)
class NewsSourceAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "category",
        "is_active",
        "is_headline_source",
        "health_status",
        "last_fetch_status",
        "last_attempt_at",
        "last_fetched_at",
        "last_accepted_count",
        "last_error_count",
    )
    list_filter = (
        "is_active",
        "category",
        "health_status",
        "last_fetch_status",
        "is_headline_source",
    )
    search_fields = ("name", "rss_url", "website_url")
    list_editable = ("is_active", "is_headline_source")
    ordering = ("name",)
    list_per_page = 40
    date_hierarchy = "created_at"
    actions = (activate_sources, deactivate_sources)
    readonly_fields = (
        "last_attempt_at",
        "last_fetched_at",
        "last_fetch_status",
        "last_fetch_error",
        "last_fetched_count",
        "last_accepted_count",
        "last_rejected_count",
        "last_duplicate_count",
        "last_error_count",
        "health_status",
        "created_at",
    )
    fieldsets = (
        (
            "منبع",
            {"fields": ("name", "rss_url", "website_url", "category")},
        ),
        (
            "وضعیت",
            {"fields": ("is_active", "is_headline_source", "health_status")},
        ),
        (
            "آخرین دریافت",
            {
                "fields": (
                    "last_attempt_at",
                    "last_fetched_at",
                    "last_fetch_status",
                    "last_fetch_error",
                    "last_fetched_count",
                    "last_accepted_count",
                    "last_rejected_count",
                    "last_duplicate_count",
                    "last_error_count",
                    "created_at",
                )
            },
        ),
    )


@admin.register(NewsTopic)
class NewsTopicAdmin(admin.ModelAdmin):
    list_display = ("name", "position", "is_active")
    list_filter = ("is_active",)
    search_fields = ("name",)
    list_editable = ("position", "is_active")
    ordering = ("position", "name")
    list_per_page = 50


@admin.register(News)
class NewsAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "source",
        "topic",
        "score",
        "is_published",
        "is_archived",
        "is_pinned",
        "published_at",
    )
    list_filter = (
        "is_published",
        "is_archived",
        "is_pinned",
        "source",
        "topic",
    )
    search_fields = ("title", "summary", "original_url")
    list_select_related = ("source", "topic")
    autocomplete_fields = ("source", "topic")
    readonly_fields = ("fetched_at",)
    date_hierarchy = "published_at"
    ordering = ("-published_at", "-id")
    list_per_page = 40
    actions = (publish_news, archive_news)
    list_editable = ("is_published", "is_archived", "is_pinned")
    fieldsets = (
        (
            "خبر",
            {
                "fields": (
                    "title",
                    "summary",
                    "source",
                    "topic",
                    "original_url",
                    "image_url",
                )
            },
        ),
        (
            "انتشار",
            {
                "fields": (
                    "score",
                    "is_published",
                    "is_archived",
                    "is_pinned",
                    "published_at",
                    "fetched_at",
                )
            },
        ),
    )


@admin.register(NewsIntake)
class NewsIntakeAdmin(admin.ModelAdmin):
    list_display = ("title", "source", "status", "topic_name", "score", "reviewed_at")
    list_filter = ("status", "source", "topic_name")
    search_fields = ("title", "original_url", "guid", "decision_reason")
    list_select_related = ("source",)
    autocomplete_fields = ("source",)
    readonly_fields = ("reviewed_at",)
    date_hierarchy = "reviewed_at"
    ordering = ("-reviewed_at", "-id")
    list_per_page = 40


@admin.register(NewsFetchRun)
class NewsFetchRunAdmin(admin.ModelAdmin):
    list_display = (
        "started_at",
        "finished_at",
        "status",
        "sources_checked",
        "fetched_count",
        "new_count",
        "accepted_count",
        "rejected_count",
        "duplicate_count",
        "error_count",
    )
    list_filter = ("status",)
    date_hierarchy = "started_at"
    ordering = ("-started_at",)
    list_per_page = 40
    readonly_fields = tuple(field.name for field in NewsFetchRun._meta.fields)

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
