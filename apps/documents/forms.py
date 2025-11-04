"""
Forms for documents app.
"""

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

MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB


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
        """Validate uploaded file."""
        file = self.cleaned_data.get("file")
        if not file:
            raise ValidationError(_("Please select a file to upload."))

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

        return file


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
        """Validate uploaded file."""
        file = self.cleaned_data.get("file")
        if not file:
            raise ValidationError(_("Please select a file to upload."))

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

        return file


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

