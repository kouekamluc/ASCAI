"""
URL configuration for jobs app.
"""

from django.urls import path
from . import views

app_name = "jobs"

urlpatterns = [
    path("", views.job_list, name="list"),
    path("create/", views.job_create, name="create"),
    path("<slug:slug>/", views.job_detail, name="detail"),
    path("<slug:slug>/edit/", views.job_edit, name="edit"),
    path("<slug:slug>/delete/", views.job_delete, name="delete"),
    path("<slug:slug>/apply/", views.job_apply, name="apply"),
    path("applications/", views.my_applications, name="my_applications"),
    path("applications/<int:pk>/", views.application_detail, name="application_detail"),
    path("my-postings/", views.my_postings, name="my_postings"),
    path("<slug:slug>/applications/", views.manage_applications, name="manage_applications"),
    path(
        "applications/<int:pk>/update-status/",
        views.update_application_status,
        name="update_application_status",
    ),
]











