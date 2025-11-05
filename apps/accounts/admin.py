"""
Admin configuration for accounts app.
"""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _
from .models import User, FailedLoginAttempt


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """Admin interface for User model."""

    list_display = [
        "email",
        "full_name",
        "role",
        "is_active",
        "date_joined",
        "last_login",
    ]
    list_filter = ["role", "is_active", "is_staff", "is_superuser", "date_joined"]
    search_fields = ["email", "first_name", "last_name"]
    ordering = ["-date_joined"]

    fieldsets = (
        (None, {"fields": ("email", "password")}),
        (
            _("Personal info"),
            {"fields": ("first_name", "last_name", "phone", "profile_picture", "bio")},
        ),
        (
            _("Permissions"),
            {
                "fields": (
                    "role",
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                ),
            },
        ),
        (_("Important dates"), {"fields": ("last_login", "date_joined")}),
    )

    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": (
                    "email",
                    "first_name",
                    "last_name",
                    "password1",
                    "password2",
                    "role",
                ),
            },
        ),
    )

    readonly_fields = ["date_joined", "last_login"]


@admin.register(FailedLoginAttempt)
class FailedLoginAttemptAdmin(admin.ModelAdmin):
    """Admin interface for FailedLoginAttempt model."""

    list_display = ["email", "ip_address", "attempted_at", "user_agent"]
    list_filter = ["attempted_at"]
    search_fields = ["email", "ip_address"]
    ordering = ["-attempted_at"]
    readonly_fields = ["email", "ip_address", "attempted_at", "user_agent"]
    date_hierarchy = "attempted_at"

    def has_add_permission(self, request):
        """Disable adding failed login attempts manually."""
        return False

    def has_change_permission(self, request, obj=None):
        """Disable editing failed login attempts."""
        return False

    actions = ["clear_attempts"]

    def clear_attempts(self, request, queryset):
        """Clear selected failed login attempts."""
        count = queryset.count()
        queryset.delete()
        self.message_user(
            request, _("Cleared %(count)d failed login attempt(s).") % {"count": count}
        )

    clear_attempts.short_description = _("Clear selected failed login attempts")
