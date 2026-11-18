from django.contrib import admin, messages
from django.utils.html import format_html

from apps.advertising.models import AdvertisementSlide


@admin.action(description="فعال‌کردن اسلایدهای انتخاب‌شده")
def activate_slides(modeladmin, request, queryset):
    updated = queryset.update(is_active=True)
    modeladmin.message_user(request, f"{updated} اسلاید فعال شد.", messages.SUCCESS)


@admin.action(description="غیرفعال‌کردن اسلایدهای انتخاب‌شده")
def deactivate_slides(modeladmin, request, queryset):
    updated = queryset.update(is_active=False)
    modeladmin.message_user(request, f"{updated} اسلاید غیرفعال شد.", messages.SUCCESS)


@admin.register(AdvertisementSlide)
class AdvertisementSlideAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "sort_order",
        "is_active",
        "starts_at",
        "ends_at",
        "desktop_preview",
        "updated_at",
    )
    list_display_links = ("title",)
    list_editable = ("sort_order", "is_active")
    list_filter = ("is_active", "starts_at", "ends_at", "created_at")
    search_fields = ("title", "subtitle", "description", "button_text", "button_url")
    ordering = ("sort_order", "-updated_at")
    list_per_page = 25
    date_hierarchy = "created_at"
    readonly_fields = ("created_at", "updated_at", "desktop_preview", "mobile_preview")
    actions = (activate_slides, deactivate_slides)
    fieldsets = (
        (
            "محتوا",
            {
                "fields": (
                    "title",
                    "subtitle",
                    "description",
                    "button_text",
                    "button_url",
                )
            },
        ),
        (
            "تصاویر",
            {
                "fields": (
                    "image_desktop",
                    "desktop_preview",
                    "image_mobile",
                    "mobile_preview",
                )
            },
        ),
        (
            "زمان‌بندی و نمایش",
            {
                "fields": (
                    "sort_order",
                    "is_active",
                    "starts_at",
                    "ends_at",
                    "created_at",
                    "updated_at",
                )
            },
        ),
    )

    @admin.display(description="پیش‌نمایش دسکتاپ")
    def desktop_preview(self, obj: AdvertisementSlide):
        if not obj.pk or not obj.image_desktop:
            return "—"
        return format_html(
            '<img src="{}" alt="" style="max-height:72px;max-width:160px;'
            'border-radius:4px;object-fit:cover;" />',
            obj.image_desktop.url,
        )

    @admin.display(description="پیش‌نمایش موبایل")
    def mobile_preview(self, obj: AdvertisementSlide):
        image = obj.image_mobile or obj.image_desktop
        if not obj.pk or not image:
            return "—"
        return format_html(
            '<img src="{}" alt="" style="max-height:72px;max-width:120px;'
            'border-radius:4px;object-fit:cover;" />',
            image.url,
        )
