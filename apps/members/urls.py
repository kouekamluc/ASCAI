"""
URL configuration for members app.
"""

from django.urls import path
from . import views

app_name = "members"

urlpatterns = [
    path("", views.member_directory, name="directory"),
    path("profile/<int:user_id>/", views.member_profile, name="profile"),
    path("export/csv/", views.export_members_csv, name="export_csv"),
    path("bulk-update/", views.bulk_update_status, name="bulk_update"),
]






