from django.contrib import admin, messages

from .models import ContactMessage


@admin.action(description="علامت‌گذاری به‌عنوان خوانده‌شده")
def mark_read(modeladmin, request, queryset):
    updated = queryset.update(is_read=True)
    modeladmin.message_user(request, f"{updated} پیام خوانده شد.", messages.SUCCESS)


@admin.action(description="علامت‌گذاری به‌عنوان خوانده‌نشده")
def mark_unread(modeladmin, request, queryset):
    updated = queryset.update(is_read=False)
    modeladmin.message_user(request, f"{updated} پیام خوانده‌نشده شد.", messages.WARNING)


@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ("subject", "name", "phone", "email", "is_read", "created_at")
    list_filter = ("is_read", "subject", "created_at")
    search_fields = ("name", "phone", "email", "subject", "message")
    readonly_fields = ("name", "phone", "email", "subject", "message", "created_at")
    date_hierarchy = "created_at"
    ordering = ("is_read", "-created_at")
    list_per_page = 40
    list_editable = ("is_read",)
    actions = (mark_read, mark_unread)
    fieldsets = (
        ("فرستنده", {"fields": ("name", "phone", "email")}),
        ("پیام", {"fields": ("subject", "message", "created_at")}),
        ("وضعیت", {"fields": ("is_read",)}),
    )

    def has_add_permission(self, request):
        return False
