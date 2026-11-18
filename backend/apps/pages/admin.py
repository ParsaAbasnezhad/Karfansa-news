from django.contrib import admin, messages
from django.utils.html import format_html

from apps.pages.models import (
    AboutFeature,
    AboutPage,
    AboutStatistic,
    AboutTeamMember,
    ContactFAQ,
    ContactPage,
)


class AboutFeatureInline(admin.TabularInline):
    model = AboutFeature
    extra = 1
    fields = ("kind", "label", "title", "body", "sort_order", "is_active")
    ordering = ("sort_order", "id")


class AboutStatisticInline(admin.TabularInline):
    model = AboutStatistic
    extra = 1
    fields = ("label", "value", "sort_order", "is_active")
    ordering = ("sort_order", "id")


class AboutTeamMemberInline(admin.StackedInline):
    model = AboutTeamMember
    extra = 0
    fields = ("name", "role", "bio", "photo", "photo_preview", "sort_order", "is_active")
    readonly_fields = ("photo_preview",)
    ordering = ("sort_order", "id")

    @admin.display(description="پیش‌نمایش")
    def photo_preview(self, obj: AboutTeamMember):
        if not obj.pk or not obj.photo:
            return "—"
        return format_html(
            '<img src="{}" alt="" style="max-height:64px;max-width:64px;border-radius:4px;object-fit:cover;" />',
            obj.photo.url,
        )


@admin.register(AboutPage)
class AboutPageAdmin(admin.ModelAdmin):
    list_display = ("title", "show_globe", "updated_at")
    search_fields = ("title", "subtitle", "intro", "seo_title")
    readonly_fields = ("created_at", "updated_at", "hero_preview", "mission_preview")
    list_per_page = 10
    inlines = (AboutFeatureInline, AboutStatisticInline, AboutTeamMemberInline)
    fieldsets = (
        (
            "هیرو",
            {
                "fields": (
                    "hero_kicker",
                    "title",
                    "subtitle",
                    "intro",
                    "hero_image",
                    "hero_preview",
                    "show_globe",
                    "primary_cta_label",
                    "primary_cta_url",
                    "secondary_cta_label",
                    "secondary_cta_url",
                )
            },
        ),
        (
            "مأموریت و چشم‌انداز",
            {
                "fields": (
                    "mission_title",
                    "mission",
                    "mission_image",
                    "mission_preview",
                    "vision_title",
                    "vision",
                    "values_title",
                    "values",
                    "goals_title",
                    "goals",
                )
            },
        ),
        (
            "روش کار و بخش پایانی",
            {
                "fields": (
                    "story_eyebrow",
                    "story_title",
                    "story_body",
                    "cta_eyebrow",
                    "cta_title",
                    "closing_text",
                )
            },
        ),
        (
            "SEO",
            {"fields": ("seo_title", "seo_description", "created_at", "updated_at")},
        ),
    )

    def has_add_permission(self, request):
        if AboutPage.objects.exists():
            return False
        return super().has_add_permission(request)

    def has_delete_permission(self, request, obj=None):
        return False

    @admin.display(description="پیش‌نمایش هیرو")
    def hero_preview(self, obj: AboutPage):
        if not obj.pk or not obj.hero_image:
            return "—"
        return format_html(
            '<img src="{}" alt="" style="max-height:90px;max-width:180px;border-radius:4px;object-fit:cover;" />',
            obj.hero_image.url,
        )

    @admin.display(description="پیش‌نمایش مأموریت")
    def mission_preview(self, obj: AboutPage):
        if not obj.pk or not obj.mission_image:
            return "—"
        return format_html(
            '<img src="{}" alt="" style="max-height:90px;max-width:180px;border-radius:4px;object-fit:cover;" />',
            obj.mission_image.url,
        )


@admin.register(AboutFeature)
class AboutFeatureAdmin(admin.ModelAdmin):
    list_display = ("title", "kind", "sort_order", "is_active", "page")
    list_editable = ("sort_order", "is_active")
    list_filter = ("kind", "is_active")
    search_fields = ("title", "label", "body")
    ordering = ("sort_order", "id")
    list_per_page = 40
    list_select_related = ("page",)
    autocomplete_fields = ("page",)


@admin.register(AboutStatistic)
class AboutStatisticAdmin(admin.ModelAdmin):
    list_display = ("label", "value", "sort_order", "is_active", "page")
    list_editable = ("sort_order", "is_active")
    list_filter = ("is_active",)
    search_fields = ("label", "value")
    ordering = ("sort_order", "id")
    list_select_related = ("page",)
    autocomplete_fields = ("page",)


@admin.register(AboutTeamMember)
class AboutTeamMemberAdmin(admin.ModelAdmin):
    list_display = ("name", "role", "sort_order", "is_active", "photo_preview", "page")
    list_editable = ("sort_order", "is_active")
    list_filter = ("is_active",)
    search_fields = ("name", "role", "bio")
    ordering = ("sort_order", "id")
    list_select_related = ("page",)
    autocomplete_fields = ("page",)
    readonly_fields = ("photo_preview",)

    @admin.display(description="تصویر")
    def photo_preview(self, obj: AboutTeamMember):
        if not obj.pk or not obj.photo:
            return "—"
        return format_html(
            '<img src="{}" alt="" style="max-height:48px;max-width:48px;border-radius:4px;object-fit:cover;" />',
            obj.photo.url,
        )


class ContactFAQInline(admin.TabularInline):
    model = ContactFAQ
    extra = 1
    fields = ("question", "answer", "sort_order", "is_active")
    ordering = ("sort_order", "id")


@admin.register(ContactPage)
class ContactPageAdmin(admin.ModelAdmin):
    list_display = ("title", "support_email", "phone", "updated_at")
    search_fields = ("title", "description", "support_email", "business_email", "phone")
    readonly_fields = ("created_at", "updated_at")
    list_per_page = 10
    inlines = (ContactFAQInline,)
    fieldsets = (
        ("محتوا", {"fields": ("title", "description", "support_text", "form_intro")}),
        (
            "راه‌های ارتباطی",
            {
                "fields": (
                    "support_email",
                    "business_email",
                    "phone",
                    "whatsapp",
                    "office_address",
                    "response_hours",
                    "map_url",
                )
            },
        ),
        (
            "شبکه‌های اجتماعی",
            {"fields": ("instagram_url", "linkedin_url", "telegram_url")},
        ),
        ("SEO", {"fields": ("seo_title", "seo_description", "created_at", "updated_at")}),
    )

    def has_add_permission(self, request):
        if ContactPage.objects.exists():
            return False
        return super().has_add_permission(request)

    def has_delete_permission(self, request, obj=None):
        return False


@admin.action(description="فعال‌کردن پرسش‌های انتخاب‌شده")
def activate_faqs(modeladmin, request, queryset):
    updated = queryset.update(is_active=True)
    modeladmin.message_user(request, f"{updated} پرسش فعال شد.", messages.SUCCESS)


@admin.action(description="غیرفعال‌کردن پرسش‌های انتخاب‌شده")
def deactivate_faqs(modeladmin, request, queryset):
    updated = queryset.update(is_active=False)
    modeladmin.message_user(request, f"{updated} پرسش غیرفعال شد.", messages.SUCCESS)


@admin.register(ContactFAQ)
class ContactFAQAdmin(admin.ModelAdmin):
    list_display = ("question", "sort_order", "is_active", "page", "updated_at")
    list_editable = ("sort_order", "is_active")
    list_filter = ("is_active",)
    search_fields = ("question", "answer")
    ordering = ("sort_order", "id")
    list_per_page = 40
    list_select_related = ("page",)
    autocomplete_fields = ("page",)
    actions = (activate_faqs, deactivate_faqs)
