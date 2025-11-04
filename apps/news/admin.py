"""
Admin configuration for news app.
"""

from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from .models import NewsCategory, NewsPost


@admin.register(NewsCategory)
class NewsCategoryAdmin(admin.ModelAdmin):
    """Admin interface for NewsCategory."""
    
    list_display = ["name", "slug", "created_at"]
    prepopulated_fields = {"slug": ("name",)}
    search_fields = ["name", "description"]


@admin.register(NewsPost)
class NewsPostAdmin(admin.ModelAdmin):
    """Admin interface for NewsPost."""
    
    list_display = [
        "title",
        "author",
        "category_type",
        "visibility",
        "is_published",
        "published_at",
        "views_count",
        "created_at",
    ]
    list_filter = [
        "is_published",
        "category_type",
        "visibility",
        "category",
        "created_at",
    ]
    search_fields = ["title", "content", "author__email"]
    prepopulated_fields = {"slug": ("title",)}
    readonly_fields = ["views_count", "created_at", "updated_at"]
    
    fieldsets = (
        (_("Content"), {
            "fields": ("title", "slug", "excerpt", "content", "featured_image")
        }),
        (_("Classification"), {
            "fields": ("category", "category_type", "visibility")
        }),
        (_("Publication"), {
            "fields": ("author", "is_published", "published_at")
        }),
        (_("Statistics"), {
            "fields": ("views_count", "created_at", "updated_at")
        }),
    )
