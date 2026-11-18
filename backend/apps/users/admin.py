from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin

from apps.users.models import OTPChallenge, ResetAuthorization, User


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    fieldsets = (
        *DjangoUserAdmin.fieldsets,
        (
            "Verified contacts",
            {
                "fields": (
                    "normalized_email",
                    "mobile",
                    "claimed_mobile",
                    "is_contact_signup",
                    "email_verified_at",
                    "mobile_verified_at",
                )
            },
        ),
    )
    list_display = (
        "username",
        "email",
        "normalized_email",
        "claimed_mobile",
        "is_staff",
        "is_active",
        "email_verified_at",
        "mobile_verified_at",
        "date_joined",
    )
    list_filter = ("is_staff", "is_superuser", "is_active", "is_contact_signup", "date_joined")
    search_fields = ("username", "email", "normalized_email", "mobile", "claimed_mobile", "first_name", "last_name")
    ordering = ("-date_joined",)
    list_per_page = 40
    readonly_fields = (*DjangoUserAdmin.readonly_fields, "email_verified_at", "mobile_verified_at")


@admin.register(OTPChallenge)
class OTPChallengeAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "user",
        "purpose",
        "channel",
        "created_at",
        "expires_at",
        "delivered_at",
        "consumed_at",
        "attempts",
    )
    list_filter = ("purpose", "channel", "created_at")
    search_fields = ("id", "user__username", "user__email", "user__normalized_email")
    list_select_related = ("user",)
    autocomplete_fields = ("user",)
    date_hierarchy = "created_at"
    ordering = ("-created_at",)
    list_per_page = 40
    readonly_fields = (
        "id",
        "user",
        "purpose",
        "channel",
        "destination_digest",
        "verifier",
        "created_at",
        "expires_at",
        "last_sent_at",
        "delivered_at",
        "attempts",
        "consumed_at",
        "invalidated_at",
    )

    def has_add_permission(self, request):
        return False


@admin.register(ResetAuthorization)
class ResetAuthorizationAdmin(admin.ModelAdmin):
    list_display = ("token_digest", "user", "created_at", "expires_at", "consumed_at")
    search_fields = ("token_digest", "user__username", "user__email")
    list_select_related = ("user",)
    autocomplete_fields = ("user",)
    date_hierarchy = "created_at"
    ordering = ("-created_at",)
    list_per_page = 40
    readonly_fields = ("token_digest", "user", "created_at", "expires_at", "consumed_at")

    def has_add_permission(self, request):
        return False
