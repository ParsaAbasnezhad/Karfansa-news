from django.contrib import admin

from .models import ContactMessage


@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):  # type: ignore[type-arg]
    list_display = ("subject", "name", "phone", "email", "is_read", "created_at")
    list_filter = ("is_read", "created_at")
    search_fields = ("name", "phone", "email", "subject", "message")
    readonly_fields = ("name", "phone", "email", "subject", "message", "created_at")
    date_hierarchy = "created_at"
    ordering = ("is_read", "-created_at")
