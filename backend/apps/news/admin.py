from django.contrib import admin

from .models import News, NewsFetchRun, NewsIntake, NewsSource, NewsTopic


@admin.register(NewsSource)
class NewsSourceAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "rss_url",
        "category",
        "is_active",
        "is_headline_source",
        "health_status",
        "last_fetch_status",
        "last_attempt_at",
        "last_fetched_at",
        "last_fetched_count",
        "last_accepted_count",
        "last_rejected_count",
        "last_duplicate_count",
        "last_error_count",
    )
    list_filter = ("is_active", "category", "health_status", "last_fetch_status")
    search_fields = ("name", "rss_url", "website_url")
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
    )


@admin.register(NewsTopic)
class NewsTopicAdmin(admin.ModelAdmin):
    list_display = ("name", "position", "is_active")
    list_filter = ("is_active",)
    search_fields = ("name",)
    ordering = ("position", "name")


@admin.register(News)
class NewsAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "source",
        "topic",
        "score",
        "is_published",
        "is_archived",
        "published_at",
    )

    list_filter = (
        "source",
        "topic",
        "is_published",
        "is_archived",
    )

    search_fields = ("title", "summary")
    readonly_fields = ("fetched_at",)
    date_hierarchy = "published_at"


@admin.register(NewsIntake)
class NewsIntakeAdmin(admin.ModelAdmin):
    list_display = ("title", "source", "status", "topic_name", "score", "reviewed_at")
    list_filter = ("status", "source", "topic_name")
    search_fields = ("title", "original_url", "guid", "decision_reason")
    readonly_fields = ("reviewed_at",)


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
    readonly_fields = tuple(field.name for field in NewsFetchRun._meta.fields)

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
