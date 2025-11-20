"""
Document library models for ASCAI platform.
"""

from django.db import models
from django.utils.translation import gettext_lazy as _
from django.conf import settings
from django.urls import reverse
from django.core.exceptions import ValidationError
from apps.core.validators import validate_document_file
import os


def document_upload_path(instance, filename):
    """Generate upload path for documents based on folder structure."""
    if instance.folder:
        folder_path = instance.folder.get_path()
        return f"documents/{folder_path}/{filename}"
    return f"documents/{filename}"


def version_upload_path(instance, filename):
    """Generate upload path for document versions."""
    if instance.document and instance.document.folder:
        folder_path = instance.document.folder.get_path()
        return f"documents/{folder_path}/versions/{instance.version_number}_{filename}"
    return f"documents/versions/{instance.version_number}_{filename}"


class DocumentTag(models.Model):
    """Tag model for categorizing documents."""

    name = models.CharField(_("name"), max_length=50, unique=True)
    slug = models.SlugField(unique=True)
    color = models.CharField(
        _("color"), max_length=7, default="#007bff", help_text=_("Hex color code")
    )
    created_at = models.DateTimeField(_("created at"), auto_now_add=True)

    class Meta:
        verbose_name = _("document tag")
        verbose_name_plural = _("document tags")
        ordering = ["name"]

    def __str__(self):
        return self.name


class DocumentFolder(models.Model):
    """Hierarchical folder structure for organizing documents."""

    class AccessLevel(models.TextChoices):
        PUBLIC = "public", _("Public")
        MEMBERS_ONLY = "members", _("Members Only")
        BOARD_ONLY = "board", _("Board Only")
        ADMIN_ONLY = "admin", _("Admin Only")

    name = models.CharField(_("name"), max_length=200)
    slug = models.SlugField(max_length=200)
    description = models.TextField(_("description"), blank=True)
    parent = models.ForeignKey(
        "self",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="children",
        verbose_name=_("parent folder"),
    )
    default_access_level = models.CharField(
        _("default access level"),
        max_length=10,
        choices=AccessLevel.choices,
        default=AccessLevel.MEMBERS_ONLY,
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="created_folders",
        verbose_name=_("created by"),
    )
    created_at = models.DateTimeField(_("created at"), auto_now_add=True)
    updated_at = models.DateTimeField(_("updated at"), auto_now=True)

    class Meta:
        verbose_name = _("document folder")
        verbose_name_plural = _("document folders")
        ordering = ["name"]
        indexes = [
            models.Index(fields=["parent", "name"]),
            models.Index(fields=["slug"]),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["parent", "slug"], name="unique_folder_slug_per_parent"
            ),
        ]

    def __str__(self):
        if self.parent:
            return f"{self.parent} / {self.name}"
        return self.name

    def get_path(self):
        """Get the full path of the folder as a string."""
        if self.parent:
            return f"{self.parent.get_path()}/{self.slug}"
        return self.slug

    def get_breadcrumbs(self):
        """Get breadcrumb trail for this folder."""
        breadcrumbs = []
        folder = self
        while folder:
            breadcrumbs.insert(0, folder)
            folder = folder.parent
        return breadcrumbs

    def can_access(self, user):
        """Check if user can access this folder."""
        if self.default_access_level == self.AccessLevel.PUBLIC:
            return True
        if not user.is_authenticated:
            return False
        if self.default_access_level == self.AccessLevel.MEMBERS_ONLY:
            return user.is_member()
        if self.default_access_level == self.AccessLevel.BOARD_ONLY:
            return user.is_board_member()
        if self.default_access_level == self.AccessLevel.ADMIN_ONLY:
            return user.is_admin()
        return False

    def can_edit(self, user):
        """Check if user can edit this folder."""
        if not user.is_authenticated:
            return False
        return user.is_board_member()

    def can_delete(self, user):
        """Check if user can delete this folder."""
        if not user.is_authenticated:
            return False
        return user.is_admin() or (
            user.is_board_member() and self.created_by == user
        )

    def clean(self):
        """Validate folder structure to prevent circular references."""
        parent = self.parent
        while parent:
            if parent == self:
                raise ValidationError(_("Cannot create circular folder references."))
            parent = parent.parent


class Document(models.Model):
    """Document model with file storage and metadata."""

    title = models.CharField(_("title"), max_length=200)
    description = models.TextField(_("description"), blank=True)
    file = models.FileField(
        _("file"), upload_to=document_upload_path, max_length=500
    )
    folder = models.ForeignKey(
        DocumentFolder,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="documents",
        verbose_name=_("folder"),
    )
    uploader = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="uploaded_documents",
        verbose_name=_("uploader"),
    )
    version_number = models.DecimalField(
        _("version number"), max_digits=5, decimal_places=1, default=1.0
    )
    tags = models.ManyToManyField(
        DocumentTag, blank=True, related_name="documents", verbose_name=_("tags")
    )
    file_size = models.PositiveIntegerField(_("file size"), default=0)
    mime_type = models.CharField(_("MIME type"), max_length=100, blank=True)
    access_level = models.CharField(
        _("access level"),
        max_length=10,
        choices=DocumentFolder.AccessLevel.choices,
        null=True,
        blank=True,
        help_text=_("Leave blank to inherit from folder"),
    )
    is_published = models.BooleanField(_("published"), default=True)
    download_count = models.PositiveIntegerField(_("download count"), default=0)
    created_at = models.DateTimeField(_("created at"), auto_now_add=True)
    updated_at = models.DateTimeField(_("updated at"), auto_now=True)

    class Meta:
        verbose_name = _("document")
        verbose_name_plural = _("documents")
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["folder", "-created_at"]),
            models.Index(fields=["uploader", "-created_at"]),
            models.Index(fields=["title"]),
            models.Index(fields=["is_published"]),
            models.Index(fields=["is_published", "created_at"]),
            models.Index(fields=["is_published", "folder"]),
        ]

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse("documents:detail", kwargs={"pk": self.pk})

    def get_access_level(self):
        """Get effective access level (inherits from folder if not set)."""
        if self.access_level:
            return self.access_level
        if self.folder:
            return self.folder.default_access_level
        # If no access_level and no folder, default to PUBLIC for backward compatibility
        # Documents in root without explicit access should be publicly accessible
        return DocumentFolder.AccessLevel.PUBLIC

    def can_view(self, user):
        """Check if user can view this document."""
        effective_level = self.get_access_level()
        if effective_level == DocumentFolder.AccessLevel.PUBLIC:
            return True
        if not user.is_authenticated:
            return False
        if effective_level == DocumentFolder.AccessLevel.MEMBERS_ONLY:
            return user.is_member()
        if effective_level == DocumentFolder.AccessLevel.BOARD_ONLY:
            return user.is_board_member()
        if effective_level == DocumentFolder.AccessLevel.ADMIN_ONLY:
            return user.is_admin()
        return False

    def can_download(self, user):
        """Check if user can download this document."""
        return self.can_view(user)

    def can_edit(self, user):
        """Check if user can edit this document."""
        if not user.is_authenticated:
            return False
        return (
            user.is_board_member()
            or (user == self.uploader and user.is_member())
        )

    def can_delete(self, user):
        """Check if user can delete this document."""
        if not user.is_authenticated:
            return False
        return user.is_admin() or (
            user.is_board_member() and user == self.uploader
        )
    
    def clean(self):
        """Validate document file."""
        super().clean()
        if self.file:
            validate_document_file(self.file)

    def get_file_extension(self):
        """Get file extension."""
        return os.path.splitext(self.file.name)[1].lower()

    def get_file_type(self):
        """Get human-readable file type."""
        ext = self.get_file_extension()
        type_map = {
            ".pdf": "PDF Document",
            ".doc": "Word Document",
            ".docx": "Word Document",
            ".xls": "Excel Spreadsheet",
            ".xlsx": "Excel Spreadsheet",
            ".ppt": "PowerPoint Presentation",
            ".pptx": "PowerPoint Presentation",
            ".txt": "Text File",
            ".zip": "Archive",
            ".rar": "Archive",
            ".jpg": "Image",
            ".jpeg": "Image",
            ".png": "Image",
            ".gif": "Image",
        }
        return type_map.get(ext, "Unknown")

    def save(self, *args, **kwargs):
        """Override save to set file size and MIME type."""
        if self.file:
            try:
                # Get file size
                if hasattr(self.file, "size") and self.file.size:
                    self.file_size = self.file.size
                elif hasattr(self.file, "file") and hasattr(self.file.file, "size"):
                    self.file_size = self.file.file.size
                
                # Get MIME type
                if hasattr(self.file, "content_type") and self.file.content_type:
                    self.mime_type = self.file.content_type
                else:
                    # Try to detect from file extension
                    import mimetypes
                    ext = self.get_file_extension()
                    mime_type, _ = mimetypes.guess_type(f"file{ext}")
                    if mime_type:
                        self.mime_type = mime_type
            except Exception:
                # If we can't get file info, continue anyway
                pass
        super().save(*args, **kwargs)


class DocumentVersion(models.Model):
    """Historical versions of documents."""

    document = models.ForeignKey(
        Document,
        on_delete=models.CASCADE,
        related_name="versions",
        verbose_name=_("document"),
    )
    version_number = models.DecimalField(
        _("version number"), max_digits=5, decimal_places=1
    )
    file = models.FileField(
        _("file"), upload_to=version_upload_path, max_length=500
    )
    file_size = models.PositiveIntegerField(_("file size"), default=0)
    mime_type = models.CharField(_("MIME type"), max_length=100, blank=True)
    changelog = models.TextField(
        _("changelog"), blank=True, help_text=_("What changed in this version")
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="document_versions",
        verbose_name=_("created by"),
    )
    created_at = models.DateTimeField(_("created at"), auto_now_add=True)

    class Meta:
        verbose_name = _("document version")
        verbose_name_plural = _("document versions")
        ordering = ["-version_number"]
        indexes = [
            models.Index(fields=["document", "-version_number"]),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["document", "version_number"],
                name="unique_version_per_document",
            ),
        ]

    def __str__(self):
        return f"{self.document.title} v{self.version_number}"

    def can_download(self, user):
        """Check if user can download this version."""
        return self.document.can_download(user)

    def save(self, *args, **kwargs):
        """Override save to set file size and MIME type."""
        if self.file:
            try:
                # Get file size
                if hasattr(self.file, "size") and self.file.size:
                    self.file_size = self.file.size
                elif hasattr(self.file, "file") and hasattr(self.file.file, "size"):
                    self.file_size = self.file.file.size
                
                # Get MIME type
                if hasattr(self.file, "content_type") and self.file.content_type:
                    self.mime_type = self.file.content_type
                else:
                    # Try to detect from file extension
                    import mimetypes
                    file_name = self.file.name if hasattr(self.file, "name") else ""
                    mime_type, _ = mimetypes.guess_type(file_name)
                    if mime_type:
                        self.mime_type = mime_type
            except Exception:
                # If we can't get file info, continue anyway
                pass
        super().save(*args, **kwargs)


class DocumentPermission(models.Model):
    """Granular permissions for individual documents."""

    class PermissionType(models.TextChoices):
        VIEW = "view", _("View")
        DOWNLOAD = "download", _("Download")
        EDIT = "edit", _("Edit")
        DELETE = "delete", _("Delete")

    document = models.ForeignKey(
        Document,
        on_delete=models.CASCADE,
        related_name="permissions",
        verbose_name=_("document"),
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="document_permissions",
        verbose_name=_("user"),
    )
    permission_type = models.CharField(
        _("permission type"),
        max_length=10,
        choices=PermissionType.choices,
    )
    granted = models.BooleanField(_("granted"), default=True)
    created_at = models.DateTimeField(_("created at"), auto_now_add=True)

    class Meta:
        verbose_name = _("document permission")
        verbose_name_plural = _("document permissions")
        ordering = ["document", "user"]
        indexes = [
            models.Index(fields=["document", "user"]),
            models.Index(fields=["user", "permission_type"]),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["document", "user", "permission_type"],
                name="unique_document_user_permission",
            ),
        ]

    def __str__(self):
        user_str = self.user.email if self.user else "Unknown"
        status = "Granted" if self.granted else "Denied"
        return f"{self.document.title} - {user_str} - {self.get_permission_type_display()} ({status})"


class FolderPermission(models.Model):
    """Granular permissions for folders."""

    class PermissionType(models.TextChoices):
        VIEW = "view", _("View")
        CREATE = "create", _("Create Documents")
        EDIT = "edit", _("Edit")
        DELETE = "delete", _("Delete")

    folder = models.ForeignKey(
        DocumentFolder,
        on_delete=models.CASCADE,
        related_name="permissions",
        verbose_name=_("folder"),
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="folder_permissions",
        verbose_name=_("user"),
    )
    permission_type = models.CharField(
        _("permission type"),
        max_length=10,
        choices=PermissionType.choices,
    )
    granted = models.BooleanField(_("granted"), default=True)
    created_at = models.DateTimeField(_("created at"), auto_now_add=True)

    class Meta:
        verbose_name = _("folder permission")
        verbose_name_plural = _("folder permissions")
        ordering = ["folder", "user"]
        indexes = [
            models.Index(fields=["folder", "user"]),
            models.Index(fields=["user", "permission_type"]),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["folder", "user", "permission_type"],
                name="unique_folder_user_permission",
            ),
        ]

    def __str__(self):
        user_str = self.user.email if self.user else "Unknown"
        status = "Granted" if self.granted else "Denied"
        return f"{self.folder.name} - {user_str} - {self.get_permission_type_display()} ({status})"
