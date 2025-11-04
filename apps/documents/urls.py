"""
URL configuration for documents app.
"""

from django.urls import path
from . import views

app_name = "documents"

urlpatterns = [
    # Document views
    path("", views.document_list, name="list"),
    path("upload/", views.document_upload, name="upload"),
    path("<int:pk>/", views.document_detail, name="detail"),
    path("<int:pk>/edit/", views.document_edit, name="edit"),
    path("<int:pk>/delete/", views.document_delete, name="delete"),
    path("<int:pk>/download/", views.document_download, name="download"),
    path("<int:pk>/upload-version/", views.document_upload_version, name="upload_version"),
    
    # Version views
    path("<int:pk>/version/<str:version_number>/download/", views.version_download, name="version_download"),
    path("<int:pk>/version/<str:version_number>/rollback/", views.version_rollback, name="version_rollback"),
    
    # Folder views
    path("folder/create/", views.folder_create, name="folder_create"),
    path("folder/<int:pk>/edit/", views.folder_edit, name="folder_edit"),
    path("folder/<int:pk>/delete/", views.folder_delete, name="folder_delete"),
    
    # Tag management
    path("tags/", views.tag_list, name="tag_list"),
    path("tags/create/", views.tag_create, name="tag_create"),
    path("tags/<int:pk>/edit/", views.tag_edit, name="tag_edit"),
    path("tags/<int:pk>/delete/", views.tag_delete, name="tag_delete"),
]

