"""
Admin interface for content app.
"""

from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from django.utils.html import format_html
from .models import (
    University,
    ExchangeProgram,
    Testimonial,
    UsefulLinkCategory,
    UsefulLink,
    ContactInfo,
    OfficeHours,
)


@admin.register(University)
class UniversityAdmin(admin.ModelAdmin):
    """Admin for universities."""
    list_display = ['name', 'location', 'has_logo', 'has_image', 'is_active', 'display_order', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'location', 'description']
    list_editable = ['is_active', 'display_order']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        (_("Basic Information"), {
            'fields': ('name', 'url', 'description', 'location')
        }),
        (_("Images"), {
            'fields': ('logo', 'image'),
            'description': _('Logo is displayed in lists, image is for featured display')
        }),
        (_("Display Settings"), {
            'fields': ('is_active', 'display_order')
        }),
        (_("Metadata"), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def has_logo(self, obj):
        """Check if university has a logo."""
        return bool(obj.logo)
    has_logo.boolean = True
    has_logo.short_description = _("Has Logo")
    
    def has_image(self, obj):
        """Check if university has an image."""
        return bool(obj.image)
    has_image.boolean = True
    has_image.short_description = _("Has Image")


@admin.register(ExchangeProgram)
class ExchangeProgramAdmin(admin.ModelAdmin):
    """Admin for exchange programs."""
    list_display = ['name', 'is_active', 'display_order', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'description']
    list_editable = ['is_active', 'display_order']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        (_("Basic Information"), {
            'fields': ('name', 'description', 'url', 'icon')
        }),
        (_("Display Settings"), {
            'fields': ('is_active', 'display_order')
        }),
        (_("Metadata"), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Testimonial)
class TestimonialAdmin(admin.ModelAdmin):
    """Admin for testimonials."""
    list_display = ['display_name', 'display_university', 'is_featured', 'is_active', 'display_order', 'created_at']
    list_filter = ['is_featured', 'is_active', 'created_at']
    search_fields = ['name', 'content', 'member__first_name', 'member__last_name', 'university']
    list_editable = ['is_featured', 'is_active', 'display_order']
    readonly_fields = ['created_at', 'updated_at']
    autocomplete_fields = ['member']
    
    fieldsets = (
        (_("Content"), {
            'fields': ('member', 'name', 'university', 'content', 'photo')
        }),
        (_("Display Settings"), {
            'fields': ('is_featured', 'is_active', 'display_order')
        }),
        (_("Metadata"), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def display_name(self, obj):
        """Display name in list."""
        return obj.display_name
    display_name.short_description = _("Name")

    def display_university(self, obj):
        """Display university in list."""
        return obj.display_university or "-"
    display_university.short_description = _("University")


@admin.register(UsefulLinkCategory)
class UsefulLinkCategoryAdmin(admin.ModelAdmin):
    """Admin for useful link categories."""
    list_display = ['name', 'slug', 'is_active', 'display_order', 'link_count']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'description']
    list_editable = ['is_active', 'display_order']
    prepopulated_fields = {'slug': ('name',)}
    readonly_fields = ['created_at']

    def link_count(self, obj):
        """Count of links in this category."""
        return obj.links.count()
    link_count.short_description = _("Links")


@admin.register(UsefulLink)
class UsefulLinkAdmin(admin.ModelAdmin):
    """Admin for useful links."""
    list_display = ['name', 'category', 'url', 'is_external', 'is_active', 'display_order']
    list_filter = ['category', 'is_external', 'is_active', 'created_at']
    search_fields = ['name', 'url', 'description']
    list_editable = ['is_active', 'display_order']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        (_("Basic Information"), {
            'fields': ('category', 'name', 'url', 'description', 'icon')
        }),
        (_("Display Settings"), {
            'fields': ('is_external', 'is_active', 'display_order')
        }),
        (_("Metadata"), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(ContactInfo)
class ContactInfoAdmin(admin.ModelAdmin):
    """Admin for contact information."""
    list_display = ['label', 'contact_type', 'email', 'phone', 'is_active', 'display_order']
    list_filter = ['contact_type', 'is_active', 'created_at']
    search_fields = ['label', 'email', 'phone', 'description']
    list_editable = ['is_active', 'display_order']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        (_("Contact Information"), {
            'fields': ('contact_type', 'label', 'email', 'phone', 'description')
        }),
        (_("Display Settings"), {
            'fields': ('is_active', 'display_order')
        }),
        (_("Metadata"), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(OfficeHours)
class OfficeHoursAdmin(admin.ModelAdmin):
    """Admin for office hours."""
    list_display = ['day', 'time_display', 'is_closed', 'notes', 'is_active', 'display_order']
    list_filter = ['day', 'is_closed', 'is_active']
    list_editable = ['is_active', 'display_order']
    
    fieldsets = (
        (_("Schedule"), {
            'fields': ('day', 'start_time', 'end_time', 'is_closed', 'notes')
        }),
        (_("Display Settings"), {
            'fields': ('is_active', 'display_order')
        }),
    )

    def time_display(self, obj):
        """Display time range."""
        if obj.is_closed:
            return _("Closed")
        return f"{obj.start_time.strftime('%H:%M')} - {obj.end_time.strftime('%H:%M')}"
    time_display.short_description = _("Hours")
