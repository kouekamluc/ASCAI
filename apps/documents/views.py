"""
Views for documents app.
"""

from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.paginator import Paginator
from django.db.models import Q, Count
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.contrib import messages
from django.utils import timezone
from django.http import FileResponse, Http404, HttpResponse
from django.conf import settings
from django.core.cache import cache
import os

from .models import (
    Document,
    DocumentFolder,
    DocumentVersion,
    DocumentTag,
    DocumentPermission,
    FolderPermission,
)
from .forms import (
    DocumentUploadForm,
    DocumentEditForm,
    DocumentVersionUploadForm,
    FolderForm,
    DocumentPermissionForm,
    FolderPermissionForm,
    DocumentTagForm,
)


def check_permission_helper(user, document=None, folder=None, permission="view"):
    """Helper function to check document/folder permissions."""
    if not user.is_authenticated:
        return False

    # Check folder-level permissions first
    if folder:
        folder_perms = FolderPermission.objects.filter(
            folder=folder, user=user, granted=True
        )
        if permission == "view":
            if folder_perms.filter(permission_type="view").exists():
                return True
        elif permission == "create":
            if folder_perms.filter(permission_type="create").exists():
                return True
        elif permission == "edit":
            if folder_perms.filter(permission_type="edit").exists():
                return True
        elif permission == "delete":
            if folder_perms.filter(permission_type="delete").exists():
                return True

        # Check default folder access
        if not folder.can_access(user):
            return False

    # Check document-level permissions
    if document:
        doc_perms = DocumentPermission.objects.filter(
            document=document, user=user, granted=True
        )
        if permission == "view":
            if doc_perms.filter(permission_type="view").exists():
                return True
        elif permission == "download":
            if doc_perms.filter(permission_type="download").exists():
                return True
        elif permission == "edit":
            if doc_perms.filter(permission_type="edit").exists():
                return True
        elif permission == "delete":
            if doc_perms.filter(permission_type="delete").exists():
                return True

        # Check default document access
        if permission == "view" or permission == "download":
            return document.can_view(user)
        elif permission == "edit":
            return document.can_edit(user)
        elif permission == "delete":
            return document.can_delete(user)

    return False


def document_list(request):
    """List all documents with folder navigation and search."""
    folder_id = request.GET.get("folder")
    search_query = request.GET.get("search", "")
    tag_id = request.GET.get("tag")
    file_type = request.GET.get("file_type")

    # Get current folder
    current_folder = None
    if folder_id:
        try:
            current_folder = DocumentFolder.objects.get(id=folder_id)
            if not current_folder.can_access(request.user):
                messages.error(request, _("You don't have permission to access this folder."))
                return redirect("documents:list")
        except DocumentFolder.DoesNotExist:
            pass

    # Base queryset - only published documents accessible to user
    documents = Document.objects.filter(is_published=True).select_related('uploader', 'folder').prefetch_related('tags')

    # Filter by folder
    if current_folder:
        documents = documents.filter(folder=current_folder)
    else:
        documents = documents.filter(folder__isnull=True)

    # Search - apply before permission filtering for efficiency
    if search_query:
        documents = documents.filter(
            Q(title__icontains=search_query)
            | Q(description__icontains=search_query)
            | Q(tags__name__icontains=search_query)
        ).distinct()

    # Filter by tag
    if tag_id:
        try:
            tag = DocumentTag.objects.get(id=tag_id)
            documents = documents.filter(tags=tag)
        except DocumentTag.DoesNotExist:
            pass

    # Filter by file type
    if file_type:
        documents = documents.filter(file__iendswith=f".{file_type}")

    # Ordering
    documents = documents.order_by("-created_at")

    # Permission filtering - check can_view for each document
    # This is necessary because access level can be inherited from folders
    # and we need to respect folder permissions as well
    accessible_docs = []
    for doc in documents:
        if doc.can_view(request.user):
            accessible_docs.append(doc.id)
    
    # If no accessible docs, return empty queryset
    if accessible_docs:
        documents = Document.objects.filter(id__in=accessible_docs).order_by("-created_at")
    else:
        documents = Document.objects.none()

    # Pagination
    paginator = Paginator(documents, 20)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    # Get folders accessible to user
    folders = DocumentFolder.objects.all()
    accessible_folders = []
    for folder in folders:
        if folder.can_access(request.user):
            accessible_folders.append(folder)

    # Get all tags (cache this queryset)
    # Gracefully handle Redis connection errors
    cache_key = 'document_tags_list'
    try:
        tags = cache.get(cache_key)
        if tags is None:
            tags = list(DocumentTag.objects.annotate(
                document_count=Count("documents")
            ).order_by("name"))
            try:
                cache.set(cache_key, tags, 60 * 15)  # Cache for 15 minutes
            except Exception:
                pass  # Cache not available, continue without caching
    except Exception:
        # Redis not available, fetch directly from database
        tags = list(DocumentTag.objects.annotate(
            document_count=Count("documents")
        ).order_by("name"))

    context = {
        "page_obj": page_obj,
        "current_folder": current_folder,
        "folders": accessible_folders,
        "tags": tags,
        "search_query": search_query,
        "tag_id": tag_id,
        "file_type": file_type,
    }

    return render(request, "documents/list.html", context)


def document_detail(request, pk):
    """Detail view for a document."""
    document = get_object_or_404(Document, pk=pk)

    # Check permissions
    if not document.can_view(request.user):
        messages.error(request, _("You don't have permission to view this document."))
        return redirect("documents:list")

    # Get versions
    versions = document.versions.all().order_by("-version_number")

    # Get permissions for this document
    doc_permissions = document.permissions.all() if request.user.is_admin() else None

    context = {
        "document": document,
        "versions": versions,
        "permissions": doc_permissions,
    }

    return render(request, "documents/detail.html", context)


@login_required
def document_upload(request):
    """Upload a new document."""
    if request.method == "POST":
        form = DocumentUploadForm(request.POST, request.FILES, user=request.user)
        if form.is_valid():
            document = form.save(commit=False)
            document.uploader = request.user

            # File metadata will be set in model's save() method
            document.save()
            form.save_m2m()  # Save tags

            # Create initial version - file metadata will be set in save()
            version = DocumentVersion(
                document=document,
                version_number=document.version_number,
                file=document.file,
                changelog=_("Initial version"),
                created_by=request.user,
            )
            version.save()

            messages.success(request, _("Document uploaded successfully."))
            return redirect("documents:detail", pk=document.pk)
    else:
        form = DocumentUploadForm(user=request.user)

    # Get accessible folders for display
    folders = DocumentFolder.objects.all()
    accessible_folders = []
    for folder in folders:
        if folder.can_access(request.user):
            accessible_folders.append(folder)

    context = {
        "form": form,
        "folders": accessible_folders,
    }

    return render(request, "documents/upload.html", context)


@login_required
def document_edit(request, pk):
    """Edit document metadata."""
    document = get_object_or_404(Document, pk=pk)

    # Check permissions
    if not document.can_edit(request.user):
        messages.error(request, _("You don't have permission to edit this document."))
        return redirect("documents:detail", pk=document.pk)

    if request.method == "POST":
        form = DocumentEditForm(
            request.POST, request.FILES, instance=document, user=request.user
        )
        if form.is_valid():
            form.save()
            messages.success(request, _("Document updated successfully."))
            return redirect("documents:detail", pk=document.pk)
    else:
        form = DocumentEditForm(instance=document, user=request.user)

    context = {
        "form": form,
        "document": document,
    }

    return render(request, "documents/edit.html", context)


@login_required
def document_delete(request, pk):
    """Delete a document."""
    document = get_object_or_404(Document, pk=pk)

    # Check permissions
    if not document.can_delete(request.user):
        messages.error(request, _("You don't have permission to delete this document."))
        return redirect("documents:detail", pk=document.pk)

    if request.method == "POST":
        document_title = document.title
        document.delete()
        messages.success(
            request, _("Document '%(title)s' deleted successfully.") % {"title": document_title}
        )
        return redirect("documents:list")

    context = {
        "document": document,
    }

    return render(request, "documents/delete_confirm.html", context)


def document_download(request, pk):
    """Download a document."""
    document = get_object_or_404(Document, pk=pk)

    # Check permissions
    if not document.can_download(request.user):
        messages.error(request, _("You don't have permission to download this document."))
        return redirect("documents:detail", pk=document.pk)

    if not document.file:
        raise Http404(_("File not found"))

    # Increment download count
    document.download_count += 1
    document.save(update_fields=["download_count"])

    # Serve file
    try:
        file_path = document.file.path if hasattr(document.file, 'path') else None
        if file_path and os.path.exists(file_path):
            file_handle = open(file_path, 'rb')
            response = FileResponse(file_handle, content_type=document.mime_type or 'application/octet-stream')
            filename = f"{document.title}{document.get_file_extension()}"
            response["Content-Disposition"] = f'attachment; filename="{filename}"'
            return response
        else:
            # Try using the file storage backend
            file_handle = document.file.open('rb')
            response = FileResponse(file_handle, content_type=document.mime_type or 'application/octet-stream')
            filename = f"{document.title}{document.get_file_extension()}"
            response["Content-Disposition"] = f'attachment; filename="{filename}"'
            return response
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error downloading document {pk}: {str(e)}")
        raise Http404(_("File not found"))


@login_required
def document_upload_version(request, pk):
    """Upload a new version of a document."""
    document = get_object_or_404(Document, pk=pk)

    # Check permissions
    if not document.can_edit(request.user):
        messages.error(request, _("You don't have permission to update this document."))
        return redirect("documents:detail", pk=document.pk)

    if request.method == "POST":
        form = DocumentVersionUploadForm(request.POST, request.FILES)
        if form.is_valid():
            # Calculate new version number
            latest_version = document.versions.order_by("-version_number").first()
            if latest_version:
                new_version = float(latest_version.version_number) + 1.0
            else:
                new_version = float(document.version_number) + 1.0

            # Save new file to document
            new_file = form.cleaned_data["file"]
            old_file = document.file

            document.file = new_file
            document.version_number = new_version
            # File metadata will be set in model's save() method
            document.save()

            # Create version record - file metadata will be set in save()
            version = DocumentVersion(
                document=document,
                version_number=new_version,
                file=new_file,
                changelog=form.cleaned_data.get("changelog", ""),
                created_by=request.user,
            )
            version.save()

            # Optionally delete old file
            if old_file and old_file != new_file:
                try:
                    if os.path.isfile(old_file.path):
                        os.remove(old_file.path)
                except Exception:
                    pass  # Ignore deletion errors

            messages.success(request, _("New version uploaded successfully."))
            return redirect("documents:detail", pk=document.pk)
    else:
        form = DocumentVersionUploadForm()

    context = {
        "form": form,
        "document": document,
    }

    return render(request, "documents/upload_version.html", context)


def version_download(request, pk, version_number):
    """Download a specific version of a document."""
    document = get_object_or_404(Document, pk=pk)

    # Check permissions
    if not document.can_download(request.user):
        messages.error(request, _("You don't have permission to download this document."))
        return redirect("documents:detail", pk=document.pk)

    try:
        # Convert version_number to Decimal for comparison
        from decimal import Decimal
        version_decimal = Decimal(str(version_number))
        version = document.versions.get(version_number=version_decimal)
    except (DocumentVersion.DoesNotExist, ValueError):
        raise Http404(_("Version not found"))

    if not version.file:
        raise Http404(_("File not found"))

    try:
        file_path = version.file.path if hasattr(version.file, 'path') else None
        if file_path and os.path.exists(file_path):
            file_handle = open(file_path, 'rb')
            response = FileResponse(file_handle, content_type=version.mime_type or 'application/octet-stream')
            file_ext = os.path.splitext(version.file.name)[1]
            filename = f"{document.title}_v{version_number}{file_ext}"
            response["Content-Disposition"] = f'attachment; filename="{filename}"'
            return response
        else:
            # Try using the file storage backend
            file_handle = version.file.open('rb')
            response = FileResponse(file_handle, content_type=version.mime_type or 'application/octet-stream')
            file_ext = os.path.splitext(version.file.name)[1]
            filename = f"{document.title}_v{version_number}{file_ext}"
            response["Content-Disposition"] = f'attachment; filename="{filename}"'
            return response
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error downloading version {version_number} of document {pk}: {str(e)}")
        raise Http404(_("File not found"))


@login_required
def version_rollback(request, pk, version_number):
    """Rollback document to a previous version."""
    document = get_object_or_404(Document, pk=pk)

    # Check permissions
    if not document.can_edit(request.user):
        messages.error(request, _("You don't have permission to edit this document."))
        return redirect("documents:detail", pk=document.pk)

    try:
        # Convert version_number to Decimal for comparison
        from decimal import Decimal
        version_decimal = Decimal(str(version_number))
        version = document.versions.get(version_number=version_decimal)
    except (DocumentVersion.DoesNotExist, ValueError):
        raise Http404(_("Version not found"))

    if request.method == "POST":
        # Calculate new version number
        latest_version = document.versions.order_by("-version_number").first()
        if latest_version:
            new_version = float(latest_version.version_number) + 1.0
        else:
            new_version = float(document.version_number) + 1.0

        # Restore file from version
        old_file = document.file
        document.file = version.file
        document.version_number = new_version
        # File metadata will be set in model's save() method, but copy from version for consistency
        document.file_size = version.file_size
        document.mime_type = version.mime_type
        document.save()

        # Create version record for rollback - file metadata will be set in save()
        rollback_version = DocumentVersion(
            document=document,
            version_number=new_version,
            file=version.file,
            changelog=_("Rolled back to version %(version)s") % {"version": version_number},
            created_by=request.user,
        )
        rollback_version.save()

        messages.success(
            request,
            _("Document rolled back to version %(version)s.") % {"version": version_number},
        )
        return redirect("documents:detail", pk=document.pk)

    context = {
        "document": document,
        "version": version,
    }

    return render(request, "documents/rollback_confirm.html", context)


@login_required
@user_passes_test(lambda u: u.is_board_member())
def folder_create(request):
    """Create a new folder."""
    if request.method == "POST":
        form = FolderForm(request.POST, user=request.user)
        if form.is_valid():
            folder = form.save(commit=False)
            folder.created_by = request.user
            folder.save()
            messages.success(request, _("Folder created successfully."))
            return redirect(f"{reverse('documents:list')}?folder={folder.id}")
    else:
        form = FolderForm(user=request.user)

    context = {
        "form": form,
        "action": _("Create"),
    }

    return render(request, "documents/folder_form.html", context)


@login_required
@user_passes_test(lambda u: u.is_board_member())
def folder_edit(request, pk):
    """Edit a folder."""
    folder = get_object_or_404(DocumentFolder, pk=pk)

    # Check permissions
    if not folder.can_edit(request.user):
        messages.error(request, _("You don't have permission to edit this folder."))
        return redirect("documents:list")

    if request.method == "POST":
        form = FolderForm(request.POST, instance=folder, user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, _("Folder updated successfully."))
            return redirect(f"{reverse('documents:list')}?folder={folder.id}")
    else:
        form = FolderForm(instance=folder, user=request.user)

    context = {
        "form": form,
        "folder": folder,
        "action": _("Edit"),
    }

    return render(request, "documents/folder_form.html", context)


@login_required
@user_passes_test(lambda u: u.is_board_member())
def folder_delete(request, pk):
    """Delete a folder."""
    folder = get_object_or_404(DocumentFolder, pk=pk)

    # Check permissions
    if not folder.can_delete(request.user):
        messages.error(request, _("You don't have permission to delete this folder."))
        return redirect("documents:list")

    # Check if folder has children or documents
    if folder.children.exists() or folder.documents.exists():
        messages.error(
            request,
            _("Cannot delete folder. It contains subfolders or documents."),
        )
        return redirect("documents:list")

    if request.method == "POST":
        folder_name = folder.name
        folder.delete()
        messages.success(
            request, _("Folder '%(name)s' deleted successfully.") % {"name": folder_name}
        )
        return redirect("documents:list")

    context = {
        "folder": folder,
    }

    return render(request, "documents/folder_delete_confirm.html", context)


# Tag Management Views
@login_required
@user_passes_test(lambda u: u.is_board_member())
def tag_list(request):
    """List all document tags."""
    from django.db.models import Count
    tags = DocumentTag.objects.annotate(
        document_count=Count("documents")
    ).order_by("name")
    return render(request, "documents/tag_list.html", {"tags": tags})


@login_required
@user_passes_test(lambda u: u.is_board_member())
def tag_create(request):
    """Create a new document tag."""
    from django.utils.text import slugify
    
    if request.method == "POST":
        form = DocumentTagForm(request.POST)
        if form.is_valid():
            tag = form.save(commit=False)
            if not tag.slug:
                base_slug = slugify(tag.name)
                slug = base_slug
                counter = 1
                while DocumentTag.objects.filter(slug=slug).exists():
                    slug = f"{base_slug}-{counter}"
                    counter += 1
                tag.slug = slug
            tag.save()
            messages.success(request, _("Tag created successfully."))
            return redirect("documents:tag_list")
    else:
        form = DocumentTagForm()
    
    return render(request, "documents/tag_form.html", {"form": form, "action": _("Create")})


@login_required
@user_passes_test(lambda u: u.is_board_member())
def tag_edit(request, pk):
    """Edit an existing document tag."""
    tag = get_object_or_404(DocumentTag, pk=pk)
    
    if request.method == "POST":
        form = DocumentTagForm(request.POST, instance=tag)
        if form.is_valid():
            form.save()
            messages.success(request, _("Tag updated successfully."))
            return redirect("documents:tag_list")
    else:
        form = DocumentTagForm(instance=tag)
    
    return render(request, "documents/tag_form.html", {
        "form": form,
        "tag": tag,
        "action": _("Edit"),
    })


@login_required
@user_passes_test(lambda u: u.is_board_member())
def tag_delete(request, pk):
    """Delete a document tag."""
    tag = get_object_or_404(DocumentTag, pk=pk)
    
    # Check if tag is used by any documents
    from django.db.models import Count
    document_count = tag.documents.count()
    
    if request.method == "POST":
        if document_count > 0:
            messages.error(
                request,
                _("Cannot delete tag. It is used by %(count)s document(s).") % {"count": document_count}
            )
        else:
            tag.delete()
            messages.success(request, _("Tag deleted successfully."))
        return redirect("documents:tag_list")
    
    return render(request, "documents/tag_delete_confirm.html", {
        "tag": tag,
        "document_count": document_count,
    })
