"""
URL configuration for ASCAI platform.
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.i18n import set_language

urlpatterns = [
    path("admin/", admin.site.urls),
    path("i18n/setlang/", set_language, name="set_language"),
    path("accounts/", include("apps.accounts.urls")),
    # Add other app URLs here as they are created
    path("", include("apps.dashboard.urls")),
    path("members/", include("apps.members.urls")),
    path("events/", include("apps.events.urls")),
    path("news/", include("apps.news.urls")),
    path("documents/", include("apps.documents.urls")),
    path("jobs/", include("apps.jobs.urls")),
    path("forums/", include("apps.forums.urls")),
    path("messaging/", include("apps.messaging.urls")),
    # path("payments/", include("apps.payments.urls")),
    # Health check endpoint (also available at /health/ via dashboard app)
    path("health/", include("apps.dashboard.urls")),
]

# Serve media files in development
# Note: Static files are automatically served by django.contrib.staticfiles in development
# We only need to manually serve media files
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
