"""
Admin configuration for documents app.
"""

from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from .models import (
    Document,
    DocumentFolder,
    DocumentVersion,
    DocumentTag,
    DocumentPermission,
    FolderPermission,
)


@admin.register(DocumentTag)
class DocumentTagAdmin(admin.ModelAdmin):
    """Admin for DocumentTag."""

    list_display = ["name", "slug", "color", "created_at"]
    search_fields = ["name", "slug"]
    prepopulated_fields = {"slug": ("name",)}
    list_filter = ["created_at"]


class FolderPermissionInline(admin.TabularInline):
    """Inline admin for folder permissions."""

    model = FolderPermission
    extra = 1
    fields = ["user", "permission_type", "granted"]


@admin.register(DocumentFolder)
class DocumentFolderAdmin(admin.ModelAdmin):
    """Admin for DocumentFolder."""

    list_display = ["name", "slug", "parent", "default_access_level", "created_by", "created_at"]
    search_fields = ["name", "slug", "description"]
    list_filter = ["default_access_level", "created_at", "parent"]
    prepopulated_fields = {"slug": ("name",)}
    inlines = [FolderPermissionInline]
    fieldsets = (
        (
            None,
            {
                "fields": ("name", "slug", "description", "parent"),
            },
        ),
        (
            _("Access"),
            {
                "fields": ("default_access_level",),
            },
        ),
        (
            _("Metadata"),
            {
                "fields": ("created_by", "created_at", "updated_at"),
            },
        ),
    )
    readonly_fields = ["created_at", "updated_at"]

    def save_model(self, request, obj, form, change):
        """Set created_by if not set."""
        if not change:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


class DocumentPermissionInline(admin.TabularInline):
    """Inline admin for document permissions."""

    model = DocumentPermission
    extra = 1
    fields = ["user", "permission_type", "granted"]


class DocumentVersionInline(admin.TabularInline):
    """Inline admin for document versions."""

    model = DocumentVersion
    extra = 0
    fields = ["version_number", "file", "changelog", "created_by", "created_at"]
    readonly_fields = ["version_number", "created_at"]
    can_delete = False

    def has_add_permission(self, request, obj=None):
        """Versions should be created via upload, not inline."""
        return False


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    """Admin for Document."""

    list_display = [
        "title",
        "folder",
        "uploader",
        "version_number",
        "file_size",
        "is_published",
        "download_count",
        "created_at",
    ]
    search_fields = ["title", "description"]
    list_filter = [
        "is_published",
        "folder",
        "access_level",
        "created_at",
        "uploader",
    ]
    readonly_fields = ["file_size", "mime_type", "download_count", "created_at", "updated_at"]
    inlines = [DocumentVersionInline, DocumentPermissionInline]
    filter_horizontal = ["tags"]
    fieldsets = (
        (
            None,
            {
                "fields": ("title", "description", "file", "folder"),
            },
        ),
        (
            _("Metadata"),
            {
                "fields": (
                    "uploader",
                    "version_number",
                    "tags",
                    "file_size",
                    "mime_type",
                ),
            },
        ),
        (
            _("Access"),
            {
                "fields": ("access_level", "is_published"),
            },
        ),
        (
            _("Statistics"),
            {
                "fields": ("download_count", "created_at", "updated_at"),
            },
        ),
    )

    def save_model(self, request, obj, form, change):
        """Set uploader if not set."""
        if not change and not obj.uploader:
            obj.uploader = request.user
        super().save_model(request, obj, form, change)


@admin.register(DocumentVersion)
class DocumentVersionAdmin(admin.ModelAdmin):
    """Admin for DocumentVersion."""

    list_display = [
        "document",
        "version_number",
        "file_size",
        "created_by",
        "created_at",
    ]
    search_fields = ["document__title", "changelog"]
    list_filter = ["created_at", "created_by"]
    readonly_fields = ["file_size", "mime_type", "created_at"]
    fieldsets = (
        (
            None,
            {
                "fields": ("document", "version_number", "file"),
            },
        ),
        (
            _("Metadata"),
            {
                "fields": ("changelog", "file_size", "mime_type", "created_by", "created_at"),
            },
        ),
    )


@admin.register(DocumentPermission)
class DocumentPermissionAdmin(admin.ModelAdmin):
    """Admin for DocumentPermission."""

    list_display = ["document", "user", "permission_type", "granted", "created_at"]
    list_filter = ["permission_type", "granted", "created_at"]
    search_fields = ["document__title", "user__email", "user__first_name", "user__last_name"]
    readonly_fields = ["created_at"]


@admin.register(FolderPermission)
class FolderPermissionAdmin(admin.ModelAdmin):
    """Admin for FolderPermission."""

    list_display = ["folder", "user", "permission_type", "granted", "created_at"]
    list_filter = ["permission_type", "granted", "created_at"]
    search_fields = ["folder__name", "user__email", "user__first_name", "user__last_name"]
    readonly_fields = ["created_at"]
