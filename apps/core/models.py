"""
Core models for ASCAI platform.
"""
from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey


class AuditLog(models.Model):
    """Audit log for tracking model changes."""
    
    class ActionType(models.TextChoices):
        CREATE = "create", _("Create")
        UPDATE = "update", _("Update")
        DELETE = "delete", _("Delete")
    
    # Content type and object reference
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')
    
    # Action details
    action = models.CharField(
        max_length=10,
        choices=ActionType.choices,
        verbose_name=_("action"),
    )
    changed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="audit_logs",
        verbose_name=_("changed by"),
    )
    
    # Change data
    old_value = models.JSONField(
        _("old value"),
        null=True,
        blank=True,
        help_text=_("Previous state of the object"),
    )
    new_value = models.JSONField(
        _("new value"),
        null=True,
        blank=True,
        help_text=_("New state of the object"),
    )
    
    # Metadata
    ip_address = models.GenericIPAddressField(
        _("IP address"),
        null=True,
        blank=True,
    )
    user_agent = models.TextField(
        _("user agent"),
        blank=True,
    )
    created_at = models.DateTimeField(
        _("created at"),
        auto_now_add=True,
        db_index=True,
    )
    
    class Meta:
        verbose_name = _("audit log")
        verbose_name_plural = _("audit logs")
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["content_type", "object_id"]),
            models.Index(fields=["changed_by", "-created_at"]),
            models.Index(fields=["action", "-created_at"]),
        ]
    
    def __str__(self):
        return f"{self.get_action_display()} - {self.content_type} #{self.object_id} by {self.changed_by or 'System'}"


class NotificationPreference(models.Model):
    """User notification preferences."""
    
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notification_preferences",
        verbose_name=_("user"),
    )
    
    # Email notification preferences
    email_news = models.BooleanField(
        _("email news notifications"),
        default=True,
        help_text=_("Receive email notifications for new news posts"),
    )
    email_forum_replies = models.BooleanField(
        _("email forum reply notifications"),
        default=True,
        help_text=_("Receive email notifications for forum replies"),
    )
    email_event_reminders = models.BooleanField(
        _("email event reminders"),
        default=True,
        help_text=_("Receive email reminders for events"),
    )
    email_member_updates = models.BooleanField(
        _("email member updates"),
        default=True,
        help_text=_("Receive email notifications for member-related updates"),
    )
    
    # In-app notification preferences
    in_app_notifications = models.BooleanField(
        _("in-app notifications"),
        default=True,
        help_text=_("Receive in-app notifications"),
    )
    
    updated_at = models.DateTimeField(
        _("updated at"),
        auto_now=True,
    )
    
    class Meta:
        verbose_name = _("notification preference")
        verbose_name_plural = _("notification preferences")
    
    def __str__(self):
        return f"Notification preferences for {self.user.email}"

