"""
Admin configuration for forums app.
"""

from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.contrib.contenttypes.admin import GenericTabularInline
from .models import (
    Category, Thread, Reply, Vote, Flag, Notification,
    ModeratorAction, UserBan
)


class ReplyInline(admin.StackedInline):
    """Inline admin for replies within threads."""
    model = Reply
    extra = 0
    readonly_fields = ["created_at", "updated_at"]


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    """Admin interface for Category."""
    
    list_display = ["name", "slug", "order", "is_active", "get_thread_count", "created_at"]
    list_filter = ["is_active", "can_view", "can_post", "created_at"]
    search_fields = ["name", "description"]
    prepopulated_fields = {"slug": ("name",)}
    readonly_fields = ["created_at", "updated_at"]
    
    fieldsets = (
        (_("Basic Information"), {
            "fields": ("name", "slug", "description", "icon")
        }),
        (_("Display"), {
            "fields": ("order", "is_active")
        }),
        (_("Permissions"), {
            "fields": ("can_view", "can_post")
        }),
        (_("Timestamps"), {
            "fields": ("created_at", "updated_at")
        }),
    )
    
    def get_thread_count(self, obj):
        """Display thread count."""
        return obj.get_thread_count()
    get_thread_count.short_description = _("Threads")


@admin.register(Thread)
class ThreadAdmin(admin.ModelAdmin):
    """Admin interface for Thread."""
    
    list_display = [
        "title", "author", "category", "is_pinned", "is_locked",
        "is_approved", "view_count", "reply_count", "created_at"
    ]
    list_filter = [
        "is_pinned", "is_locked", "is_approved",
        "category", "created_at"
    ]
    search_fields = ["title", "content", "author__email", "tags"]
    prepopulated_fields = {"slug": ("title",)}
    readonly_fields = ["view_count", "reply_count", "created_at", "updated_at", "last_activity"]
    
    fieldsets = (
        (_("Content"), {
            "fields": ("title", "slug", "content", "tags")
        }),
        (_("Classification"), {
            "fields": ("category", "author")
        }),
        (_("Status"), {
            "fields": ("is_pinned", "is_locked", "is_approved")
        }),
        (_("Statistics"), {
            "fields": ("view_count", "reply_count")
        }),
        (_("Timestamps"), {
            "fields": ("created_at", "updated_at", "last_activity")
        }),
    )
    
    inlines = [ReplyInline]
    
    actions = ["approve_threads", "lock_threads", "unlock_threads", "pin_threads", "unpin_threads"]
    
    def approve_threads(self, request, queryset):
        """Approve selected threads."""
        queryset.update(is_approved=True)
    approve_threads.short_description = _("Approve selected threads")
    
    def lock_threads(self, request, queryset):
        """Lock selected threads."""
        queryset.update(is_locked=True)
    lock_threads.short_description = _("Lock selected threads")
    
    def unlock_threads(self, request, queryset):
        """Unlock selected threads."""
        queryset.update(is_locked=False)
    unlock_threads.short_description = _("Unlock selected threads")
    
    def pin_threads(self, request, queryset):
        """Pin selected threads."""
        queryset.update(is_pinned=True)
    pin_threads.short_description = _("Pin selected threads")
    
    def unpin_threads(self, request, queryset):
        """Unpin selected threads."""
        queryset.update(is_pinned=False)
    unpin_threads.short_description = _("Unpin selected threads")


@admin.register(Reply)
class ReplyAdmin(admin.ModelAdmin):
    """Admin interface for Reply."""
    
    list_display = [
        "author", "thread", "is_approved", "is_edited",
        "created_at", "updated_at"
    ]
    list_filter = ["is_approved", "is_edited", "created_at"]
    search_fields = ["content", "author__email", "thread__title"]
    readonly_fields = ["is_edited", "created_at", "updated_at"]
    
    fieldsets = (
        (_("Content"), {
            "fields": ("thread", "author", "content", "parent_reply")
        }),
        (_("Status"), {
            "fields": ("is_approved", "is_edited")
        }),
        (_("Timestamps"), {
            "fields": ("created_at", "updated_at")
        }),
    )
    
    actions = ["approve_replies"]
    
    def approve_replies(self, request, queryset):
        """Approve selected replies."""
        queryset.update(is_approved=True)
    approve_replies.short_description = _("Approve selected replies")


@admin.register(Vote)
class VoteAdmin(admin.ModelAdmin):
    """Admin interface for Vote."""
    
    list_display = ["user", "vote_type", "content_object", "content_type", "created_at"]
    list_filter = ["vote_type", "content_type", "created_at"]
    search_fields = ["user__email"]
    readonly_fields = ["created_at"]


@admin.register(Flag)
class FlagAdmin(admin.ModelAdmin):
    """Admin interface for Flag."""
    
    list_display = [
        "reporter", "reason", "status", "content_object",
        "reviewed_by", "created_at"
    ]
    list_filter = ["reason", "status", "created_at"]
    search_fields = ["reporter__email", "description", "reviewed_by__email"]
    readonly_fields = ["created_at", "updated_at"]
    
    fieldsets = (
        (_("Report Details"), {
            "fields": ("content_type", "object_id", "reporter", "reason", "description")
        }),
        (_("Review"), {
            "fields": ("status", "reviewed_by", "reviewed_at")
        }),
        (_("Timestamps"), {
            "fields": ("created_at", "updated_at")
        }),
    )
    
    actions = ["mark_as_reviewed", "mark_as_resolved", "dismiss_flags"]
    
    def mark_as_reviewed(self, request, queryset):
        """Mark selected flags as reviewed."""
        queryset.update(status=Flag.Status.REVIEWED, reviewed_by=request.user, reviewed_at=timezone.now())
    mark_as_reviewed.short_description = _("Mark as reviewed")
    
    def mark_as_resolved(self, request, queryset):
        """Mark selected flags as resolved."""
        queryset.update(status=Flag.Status.RESOLVED, reviewed_by=request.user, reviewed_at=timezone.now())
    mark_as_resolved.short_description = _("Mark as resolved")
    
    def dismiss_flags(self, request, queryset):
        """Dismiss selected flags."""
        queryset.update(status=Flag.Status.DISMISSED, reviewed_by=request.user, reviewed_at=timezone.now())
    dismiss_flags.short_description = _("Dismiss flags")


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    """Admin interface for Notification."""
    
    list_display = [
        "recipient", "notification_type", "is_read",
        "is_emailed", "created_at"
    ]
    list_filter = ["notification_type", "is_read", "is_emailed", "created_at"]
    search_fields = ["recipient__email", "message"]
    readonly_fields = ["created_at"]
    
    actions = ["mark_as_read", "mark_as_unread"]
    
    def mark_as_read(self, request, queryset):
        """Mark selected notifications as read."""
        queryset.update(is_read=True)
    mark_as_read.short_description = _("Mark as read")
    
    def mark_as_unread(self, request, queryset):
        """Mark selected notifications as unread."""
        queryset.update(is_read=False)
    mark_as_unread.short_description = _("Mark as unread")


@admin.register(ModeratorAction)
class ModeratorActionAdmin(admin.ModelAdmin):
    """Admin interface for ModeratorAction."""
    
    list_display = [
        "moderator", "action_type", "content_object",
        "content_type", "created_at"
    ]
    list_filter = ["action_type", "created_at"]
    search_fields = ["moderator__email", "reason"]
    readonly_fields = ["created_at"]
    
    fieldsets = (
        (_("Action Details"), {
            "fields": ("moderator", "action_type", "reason")
        }),
        (_("Content"), {
            "fields": ("content_type", "object_id")
        }),
        (_("Timestamps"), {
            "fields": ("created_at",)
        }),
    )


@admin.register(UserBan)
class UserBanAdmin(admin.ModelAdmin):
    """Admin interface for UserBan."""
    
    list_display = [
        "user", "ban_type", "is_active",
        "start_date", "end_date", "banned_by"
    ]
    list_filter = ["ban_type", "is_active", "start_date"]
    search_fields = ["user__email", "reason", "banned_by__email"]
    readonly_fields = ["created_at", "start_date"]
    
    fieldsets = (
        (_("Ban Details"), {
            "fields": ("user", "ban_type", "reason")
        }),
        (_("Issuer"), {
            "fields": ("banned_by",)
        }),
        (_("Duration"), {
            "fields": ("start_date", "end_date", "is_active")
        }),
        (_("Timestamps"), {
            "fields": ("created_at",)
        }),
    )
    
    actions = ["activate_bans", "deactivate_bans"]
    
    def activate_bans(self, request, queryset):
        """Activate selected bans."""
        queryset.update(is_active=True)
    activate_bans.short_description = _("Activate selected bans")
    
    def deactivate_bans(self, request, queryset):
        """Deactivate selected bans."""
        queryset.update(is_active=False)
    deactivate_bans.short_description = _("Deactivate selected bans")
