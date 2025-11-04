"""
Admin configuration for members app.
"""

from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from .models import Member


@admin.register(Member)
class MemberAdmin(admin.ModelAdmin):
    """Admin interface for Member model."""

    list_display = [
        "user",
        "membership_number",
        "status",
        "category",
        "university",
        "joined_date",
    ]
    list_filter = [
        "status",
        "category",
        "profile_public",
        "joined_date",
        "country_of_origin",
    ]
    search_fields = [
        "user__email",
        "user__first_name",
        "user__last_name",
        "membership_number",
        "university",
        "course",
    ]
    readonly_fields = ["created_at", "updated_at", "joined_date"]
    
    fieldsets = (
        (_("User"), {"fields": ("user",)}),
        (
            _("Membership"),
            {
                "fields": (
                    "membership_number",
                    "status",
                    "category",
                    "joined_date",
                    "membership_expiry",
                )
            },
        ),
        (
            _("Academic Information"),
            {
                "fields": (
                    "university",
                    "course",
                    "year_of_study",
                    "graduation_year",
                )
            },
        ),
        (
            _("Personal Information"),
            {
                "fields": (
                    "city",
                    "country_of_origin",
                    "date_of_birth",
                    "linkedin",
                    "website",
                )
            },
        ),
        (
            _("Privacy Settings"),
            {"fields": ("profile_public", "email_public")},
        ),
        (_("Metadata"), {"fields": ("created_at", "updated_at")}),
    )
