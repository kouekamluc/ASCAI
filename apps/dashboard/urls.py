"""
URL configuration for dashboard app.
"""

from django.urls import path
from . import views

app_name = "dashboard"

urlpatterns = [
    path("", views.index_view, name="index"),
    path("dashboard/", views.home_view, name="home"),
    path("dashboard/admin/", views.admin_dashboard_view, name="admin"),
    path("dashboard/admin/api/", views.admin_dashboard_api_view, name="admin_api"),
    path("dashboard/admin/reports/export/", views.export_report_view, name="export_report"),
]

