"""
Forms for documents app.
"""

import os
import re
import mimetypes
import hashlib
from django import forms
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
from .models import (
    Document,
    DocumentFolder,
    DocumentTag,
    DocumentPermission,
    FolderPermission,
)


ALLOWED_FILE_EXTENSIONS = [
    ".pdf",
    ".doc",
    ".docx",
    ".xls",
    ".xlsx",
    ".ppt",
    ".pptx",
    ".txt",
    ".zip",
    ".rar",
    ".jpg",
    ".jpeg",
    ".png",
    ".gif",
    ".csv",
    ".rtf",
    ".odt",
    ".ods",
    ".odp",
]

# MIME type mapping for validation
ALLOWED_MIME_TYPES = {
    ".pdf": ["application/pdf"],
    ".doc": ["application/msword"],
    ".docx": ["application/vnd.openxmlformats-officedocument.wordprocessingml.document"],
    ".xls": ["application/vnd.ms-excel"],
    ".xlsx": ["application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"],
    ".ppt": ["application/vnd.ms-powerpoint"],
    ".pptx": ["application/vnd.openxmlformats-officedocument.presentationml.presentation"],
    ".txt": ["text/plain"],
    ".zip": ["application/zip"],
    ".rar": ["application/x-rar-compressed", "application/vnd.rar"],
    ".jpg": ["image/jpeg"],
    ".jpeg": ["image/jpeg"],
    ".png": ["image/png"],
    ".gif": ["image/gif"],
    ".csv": ["text/csv", "application/csv"],
    ".rtf": ["application/rtf", "text/rtf"],
    ".odt": ["application/vnd.oasis.opendocument.text"],
    ".ods": ["application/vnd.oasis.opendocument.spreadsheet"],
    ".odp": ["application/vnd.oasis.opendocument.presentation"],
}

MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB


def sanitize_filename(filename):
    """Sanitize filename to prevent path traversal and remove dangerous characters."""
    # Remove path components
    filename = os.path.basename(filename)
    # Remove or replace dangerous characters
    filename = re.sub(r'[<>:"|?*\\/]', '_', filename)
    # Remove leading/trailing dots and spaces
    filename = filename.strip('. ')
    # Limit length
    if len(filename) > 255:
        name, ext = os.path.splitext(filename)
        filename = name[:255 - len(ext)] + ext
    return filename


def get_file_hash(file):
    """Calculate SHA-256 hash of file content."""
    hash_sha256 = hashlib.sha256()
    file.seek(0)  # Reset to beginning
    for chunk in file.chunks():
        hash_sha256.update(chunk)
    file.seek(0)  # Reset again
    return hash_sha256.hexdigest()


def validate_uploaded_file(file):
    """Comprehensive file validation with security checks."""
    if not file:
        raise ValidationError(_("Please select a file to upload."))

    # Sanitize filename
    original_filename = file.name
    file.name = sanitize_filename(file.name)
    if file.name != original_filename:
        # Log filename change for security
        import logging
        logger = logging.getLogger("security")
        logger.warning(f"Filename sanitized: {original_filename} -> {file.name}")

    # Check file extension
    file_name = file.name.lower()
    file_ext = None
    for ext in ALLOWED_FILE_EXTENSIONS:
        if file_name.endswith(ext):
            file_ext = ext
            break

    if not file_ext:
        raise ValidationError(
            _(
                "File type not allowed. Allowed types: %(types)s"
                % {"types": ", ".join(ALLOWED_FILE_EXTENSIONS)}
            )
        )

    # Check file size
    if hasattr(file, "size") and file.size > MAX_FILE_SIZE:
        raise ValidationError(
            _("File size exceeds maximum allowed size of %(size)sMB")
            % {"size": MAX_FILE_SIZE // (1024 * 1024)}
        )

    # Validate MIME type
    file.seek(0)  # Reset to beginning
    detected_mime, _ = mimetypes.guess_type(file.name)
    if detected_mime:
        allowed_mimes = ALLOWED_MIME_TYPES.get(file_ext, [])
        if allowed_mimes and detected_mime not in allowed_mimes:
            raise ValidationError(
                _(
                    "File MIME type '%(mime)s' does not match file extension. "
                    "This may indicate a security issue."
                )
                % {"mime": detected_mime}
            )

    # Additional validation: check file content header
    file.seek(0)
    file_header = file.read(1024)  # Read first 1KB
    file.seek(0)

    # Basic content validation for common file types
    if file_ext == ".pdf" and not file_header.startswith(b"%PDF"):
        raise ValidationError(_("File does not appear to be a valid PDF."))
    elif file_ext in [".jpg", ".jpeg"] and not file_header.startswith(b"\xff\xd8\xff"):
        raise ValidationError(_("File does not appear to be a valid JPEG image."))
    elif file_ext == ".png" and not file_header.startswith(b"\x89PNG\r\n\x1a\n"):
        raise ValidationError(_("File does not appear to be a valid PNG image."))
    elif file_ext == ".gif" and not file_header.startswith(b"GIF87a") and not file_header.startswith(b"GIF89a"):
        raise ValidationError(_("File does not appear to be a valid GIF image."))
    elif file_ext in [".zip", ".docx", ".xlsx", ".pptx"] and not file_header.startswith(b"PK"):
        # These are ZIP-based formats
        raise ValidationError(_("File does not appear to be a valid archive format."))

    return file


class DocumentUploadForm(forms.ModelForm):
    """Form for uploading new documents."""

    class Meta:
        model = Document
        fields = [
            "title",
            "description",
            "file",
            "folder",
            "tags",
            "access_level",
            "is_published",
        ]
        widgets = {
            "title": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": _("Enter document title"),
                }
            ),
            "description": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 4,
                    "placeholder": _("Document description (optional)"),
                }
            ),
            "file": forms.FileInput(attrs={"class": "form-control"}),
            "folder": forms.Select(attrs={"class": "form-control"}),
            "tags": forms.SelectMultiple(attrs={"class": "form-control"}),
            "access_level": forms.Select(attrs={"class": "form-control"}),
            "is_published": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)
        
        # Filter folders based on user permissions
        if user:
            if user.is_admin():
                self.fields["folder"].queryset = DocumentFolder.objects.all()
            elif user.is_board_member():
                # Board members can see all folders they can access
                self.fields["folder"].queryset = DocumentFolder.objects.all()
            else:
                # Regular members can only see accessible folders
                accessible_folders = []
                for folder in DocumentFolder.objects.all():
                    if folder.can_access(user):
                        accessible_folders.append(folder.id)
                self.fields["folder"].queryset = DocumentFolder.objects.filter(
                    id__in=accessible_folders
                )
        else:
            self.fields["folder"].queryset = DocumentFolder.objects.filter(
                default_access_level=DocumentFolder.AccessLevel.PUBLIC
            )

        self.fields["tags"].queryset = DocumentTag.objects.all()
        self.fields["access_level"].choices = [
            ("", _("Inherit from folder"))
        ] + list(DocumentFolder.AccessLevel.choices)

        # Make folder optional
        self.fields["folder"].required = False

    def clean_file(self):
        """Validate uploaded file with enhanced security checks."""
        file = self.cleaned_data.get("file")
        return validate_uploaded_file(file)


class DocumentEditForm(forms.ModelForm):
    """Form for editing document metadata."""

    class Meta:
        model = Document
        fields = [
            "title",
            "description",
            "folder",
            "tags",
            "access_level",
            "is_published",
        ]
        widgets = {
            "title": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": _("Enter document title"),
                }
            ),
            "description": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 4,
                    "placeholder": _("Document description (optional)"),
                }
            ),
            "folder": forms.Select(attrs={"class": "form-control"}),
            "tags": forms.SelectMultiple(attrs={"class": "form-control"}),
            "access_level": forms.Select(attrs={"class": "form-control"}),
            "is_published": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop("user", None)
        instance = kwargs.get("instance")
        super().__init__(*args, **kwargs)

        if user:
            if user.is_admin():
                self.fields["folder"].queryset = DocumentFolder.objects.all()
            elif user.is_board_member():
                self.fields["folder"].queryset = DocumentFolder.objects.all()
            else:
                accessible_folders = []
                for folder in DocumentFolder.objects.all():
                    if folder.can_access(user):
                        accessible_folders.append(folder.id)
                self.fields["folder"].queryset = DocumentFolder.objects.filter(
                    id__in=accessible_folders
                )
        else:
            self.fields["folder"].queryset = DocumentFolder.objects.filter(
                default_access_level=DocumentFolder.AccessLevel.PUBLIC
            )

        self.fields["tags"].queryset = DocumentTag.objects.all()
        self.fields["access_level"].choices = [
            ("", _("Inherit from folder"))
        ] + list(DocumentFolder.AccessLevel.choices)
        self.fields["folder"].required = False

        # Pre-populate with current values
        if instance:
            if not instance.access_level:
                self.fields["access_level"].initial = ""


class DocumentVersionUploadForm(forms.Form):
    """Form for uploading a new version of a document."""

    file = forms.FileField(
        label=_("New file"),
        widget=forms.FileInput(attrs={"class": "form-control"}),
    )
    changelog = forms.CharField(
        label=_("Changelog"),
        required=False,
        widget=forms.Textarea(
            attrs={
                "class": "form-control",
                "rows": 3,
                "placeholder": _("Describe what changed in this version (optional)"),
            }
        ),
    )

    def clean_file(self):
        """Validate uploaded file with enhanced security checks."""
        file = self.cleaned_data.get("file")
        return validate_uploaded_file(file)


class FolderForm(forms.ModelForm):
    """Form for creating/editing folders."""

    class Meta:
        model = DocumentFolder
        fields = [
            "name",
            "slug",
            "description",
            "parent",
            "default_access_level",
        ]
        widgets = {
            "name": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": _("Folder name"),
                }
            ),
            "slug": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": _("folder-slug"),
                }
            ),
            "description": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 3,
                    "placeholder": _("Folder description (optional)"),
                }
            ),
            "parent": forms.Select(attrs={"class": "form-control"}),
            "default_access_level": forms.Select(attrs={"class": "form-control"}),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop("user", None)
        instance = kwargs.get("instance")
        super().__init__(*args, **kwargs)

        # Exclude current folder and its children from parent options to prevent circular references
        if instance:
            exclude_ids = [instance.id]
            exclude_ids.extend(
                instance.children.values_list("id", flat=True)
            )
            self.fields["parent"].queryset = DocumentFolder.objects.exclude(
                id__in=exclude_ids
            )
        else:
            self.fields["parent"].queryset = DocumentFolder.objects.all()

        self.fields["parent"].required = False

    def clean(self):
        """Validate folder structure."""
        cleaned_data = super().clean()
        parent = cleaned_data.get("parent")
        instance = self.instance

        # Check for circular references
        if parent and instance:
            current = parent
            while current:
                if current.id == instance.id:
                    raise ValidationError(
                        _("Cannot create circular folder references.")
                    )
                current = current.parent

        return cleaned_data


class DocumentPermissionForm(forms.ModelForm):
    """Form for managing document permissions."""

    class Meta:
        model = DocumentPermission
        fields = ["user", "permission_type", "granted"]
        widgets = {
            "user": forms.Select(attrs={"class": "form-control"}),
            "permission_type": forms.Select(attrs={"class": "form-control"}),
            "granted": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }

    def __init__(self, *args, **kwargs):
        document = kwargs.pop("document", None)
        super().__init__(*args, **kwargs)
        if document:
            self.instance.document = document


class FolderPermissionForm(forms.ModelForm):
    """Form for managing folder permissions."""

    class Meta:
        model = FolderPermission
        fields = ["user", "permission_type", "granted"]
        widgets = {
            "user": forms.Select(attrs={"class": "form-control"}),
            "permission_type": forms.Select(attrs={"class": "form-control"}),
            "granted": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }

    def __init__(self, *args, **kwargs):
        folder = kwargs.pop("folder", None)
        super().__init__(*args, **kwargs)
        if folder:
            self.instance.folder = folder


class DocumentTagForm(forms.ModelForm):
    """Form for creating/editing document tags."""

    class Meta:
        model = DocumentTag
        fields = ["name", "slug", "color"]
        widgets = {
            "name": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": _("Tag name"),
                }
            ),
            "slug": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": _("tag-slug"),
                }
            ),
            "color": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "type": "color",
                }
            ),
        }

