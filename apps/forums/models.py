"""
Forum models for ASCAI platform discussion system.
"""

from django.db import models
from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey, GenericRelation
from django.utils import timezone
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
from ckeditor.fields import RichTextField
from apps.core.utils import sanitize_html

# Import User model for role choices
from apps.accounts.models import User


class Category(models.Model):
    """Forum category model."""
    
    name = models.CharField(_("name"), max_length=100)
    slug = models.SlugField(unique=True)
    description = models.TextField(_("description"), blank=True)
    icon = models.CharField(_("icon"), max_length=50, blank=True, help_text="CSS class for icon")
    order = models.PositiveIntegerField(_("order"), default=0)
    is_active = models.BooleanField(_("active"), default=True)
    
    # Permissions
    can_view = models.CharField(
        max_length=10,
        choices=User.Role.choices,
        default=User.Role.PUBLIC,
    )
    can_post = models.CharField(
        max_length=10,
        choices=User.Role.choices,
        default=User.Role.MEMBER,
    )
    
    created_at = models.DateTimeField(_("created at"), auto_now_add=True)
    updated_at = models.DateTimeField(_("updated at"), auto_now=True)
    
    class Meta:
        verbose_name = _("category")
        verbose_name_plural = _("categories")
        ordering = ["order", "name"]
    
    def __str__(self):
        return self.name
    
    def get_absolute_url(self):
        return reverse("forums:category_detail", kwargs={"slug": self.slug})
    
    def get_thread_count(self):
        """Get count of approved threads in this category."""
        return self.threads.filter(is_approved=True).count()
    
    def can_user_view(self, user):
        """Check if user can view this category."""
        if self.can_view == User.Role.PUBLIC:
            return True
        if not user.is_authenticated:
            return False
        if self.can_view == User.Role.MEMBER:
            return user.is_member()
        if self.can_view == User.Role.BOARD:
            return user.is_board_member()
        return False
    
    def can_user_post(self, user):
        """Check if user can post in this category."""
        if not user.is_authenticated:
            return False
        if self.can_post == User.Role.PUBLIC:
            return True
        if self.can_post == User.Role.MEMBER:
            return user.is_member()
        if self.can_post == User.Role.BOARD:
            return user.is_board_member()
        return False


class Thread(models.Model):
    """Forum thread model."""
    
    title = models.CharField(_("title"), max_length=200)
    slug = models.SlugField(unique=True, max_length=200)
    content = RichTextField(_("content"))
    
    category = models.ForeignKey(
        Category,
        on_delete=models.CASCADE,
        related_name="threads"
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="threads"
    )
    
    # Status fields
    is_pinned = models.BooleanField(_("pinned"), default=False)
    is_locked = models.BooleanField(_("locked"), default=False)
    is_approved = models.BooleanField(_("approved"), default=True)
    
    # Statistics
    view_count = models.PositiveIntegerField(_("views"), default=0)
    reply_count = models.PositiveIntegerField(_("replies"), default=0)
    
    # Timestamps
    created_at = models.DateTimeField(_("created at"), auto_now_add=True)
    updated_at = models.DateTimeField(_("updated at"), auto_now=True)
    last_activity = models.DateTimeField(_("last activity"), auto_now_add=True)
    
    # Tags for organization
    tags = models.CharField(_("tags"), max_length=200, blank=True, help_text="Comma-separated tags")
    
    class Meta:
        verbose_name = _("thread")
        verbose_name_plural = _("threads")
        ordering = ["-is_pinned", "-last_activity"]
        indexes = [
            models.Index(fields=["-last_activity"]),
            models.Index(fields=["category"]),
            models.Index(fields=["author"]),
            models.Index(fields=["category", "is_approved", "-last_activity"]),
            models.Index(fields=["is_approved", "-created_at"]),
        ]
    
    def __str__(self):
        return self.title
    
    def get_absolute_url(self):
        return reverse("forums:thread_detail", kwargs={"slug": self.slug})
    
    def increment_view_count(self):
        """Increment view count."""
        self.view_count += 1
        self.save(update_fields=["view_count"])
    
    def update_reply_count(self):
        """Update reply count from replies."""
        if not self.pk:
            return  # Can't update if not saved yet
        new_count = self.replies.filter(is_approved=True).count()
        # Use update() to avoid triggering signals
        Thread.objects.filter(pk=self.pk).update(reply_count=new_count)
        self.reply_count = new_count
    
    def update_last_activity(self):
        """Update last activity timestamp."""
        if not self.pk:
            return  # Can't update if not saved yet
        new_activity = timezone.now()
        # Use update() to avoid triggering signals
        Thread.objects.filter(pk=self.pk).update(last_activity=new_activity)
        self.last_activity = new_activity
    
    def clean(self):
        """Validate and sanitize content."""
        super().clean()
        # Sanitize HTML content
        if self.content:
            self.content = sanitize_html(self.content)
    
    def save(self, *args, **kwargs):
        """Override save to sanitize content."""
        self.full_clean()
        super().save(*args, **kwargs)


class Reply(models.Model):
    """Forum reply model."""
    
    thread = models.ForeignKey(
        Thread,
        on_delete=models.CASCADE,
        related_name="replies"
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="replies"
    )
    content = RichTextField(_("content"))
    
    # Nested replies support
    parent_reply = models.ForeignKey(
        "self",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="child_replies"
    )
    
    # Status
    is_approved = models.BooleanField(_("approved"), default=True)
    is_edited = models.BooleanField(_("edited"), default=False)
    
    created_at = models.DateTimeField(_("created at"), auto_now_add=True)
    updated_at = models.DateTimeField(_("updated at"), auto_now=True)
    
    class Meta:
        verbose_name = _("reply")
        verbose_name_plural = _("replies")
        ordering = ["created_at"]
        indexes = [
            models.Index(fields=["thread", "created_at"]),
            models.Index(fields=["author"]),
        ]
    
    def __str__(self):
        return f"Reply by {self.author.email} to {self.thread.title[:50]}"
    
    def clean(self):
        """Validate and sanitize content."""
        super().clean()
        # Sanitize HTML content
        if self.content:
            self.content = sanitize_html(self.content)
    
    def save(self, *args, **kwargs):
        """Override save to handle edited flag and sanitize content."""
        self.full_clean()
        if self.pk:
            self.is_edited = True
        super().save(*args, **kwargs)
        
        # Note: Thread statistics are updated via signals (update_thread_on_reply)
        # to avoid duplicate updates and potential recursion


class Vote(models.Model):
    """Content voting model."""
    
    class VoteType(models.TextChoices):
        UPVOTE = "upvote", _("Upvote")
        DOWNVOTE = "downvote", _("Downvote")
    
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey("content_type", "object_id")
    
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="votes"
    )
    vote_type = models.CharField(
        max_length=10,
        choices=VoteType.choices
    )
    created_at = models.DateTimeField(_("created at"), auto_now_add=True)
    
    class Meta:
        verbose_name = _("vote")
        verbose_name_plural = _("votes")
        unique_together = [["content_type", "object_id", "user"]]
        indexes = [
            models.Index(fields=["content_type", "object_id"]),
        ]
    
    def __str__(self):
        return f"{self.vote_type} by {self.user.email}"


class Flag(models.Model):
    """Content flagging/reporting model."""
    
    class Reason(models.TextChoices):
        SPAM = "spam", _("Spam")
        INAPPROPRIATE = "inappropriate", _("Inappropriate Content")
        HARASSMENT = "harassment", _("Harassment")
        COPYRIGHT = "copyright", _("Copyright Violation")
        OTHER = "other", _("Other")
    
    class Status(models.TextChoices):
        PENDING = "pending", _("Pending")
        REVIEWED = "reviewed", _("Reviewed")
        RESOLVED = "resolved", _("Resolved")
        DISMISSED = "dismissed", _("Dismissed")
    
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey("content_type", "object_id")
    
    reporter = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="flags_reported"
    )
    reason = models.CharField(
        max_length=20,
        choices=Reason.choices
    )
    description = models.TextField(_("description"), blank=True)
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING
    )
    
    reviewed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="flags_reviewed"
    )
    reviewed_at = models.DateTimeField(_("reviewed at"), null=True, blank=True)
    
    created_at = models.DateTimeField(_("created at"), auto_now_add=True)
    updated_at = models.DateTimeField(_("updated at"), auto_now=True)
    
    class Meta:
        verbose_name = _("flag")
        verbose_name_plural = _("flags")
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["status"]),
            models.Index(fields=["content_type", "object_id"]),
        ]
    
    def __str__(self):
        return f"Flag by {self.reporter.email} - {self.reason}"


class Notification(models.Model):
    """Notification model for forum activities."""
    
    class NotificationType(models.TextChoices):
        REPLY = "reply", _("Reply")
        MENTION = "mention", _("Mention")
        VOTE = "vote", _("Vote")
        MODERATION = "moderation", _("Moderation")
        THREAD_LOCKED = "thread_locked", _("Thread Locked")
        THREAD_PINNED = "thread_pinned", _("Thread Pinned")
        CONTENT_APPROVED = "approved", _("Content Approved")
        CONTENT_REJECTED = "rejected", _("Content Rejected")
    
    recipient = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="notifications"
    )
    notification_type = models.CharField(
        max_length=20,
        choices=NotificationType.choices
    )
    
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey("content_type", "object_id")
    
    message = models.TextField(_("message"))
    is_read = models.BooleanField(_("read"), default=False)
    is_emailed = models.BooleanField(_("emailed"), default=False)
    
    created_at = models.DateTimeField(_("created at"), auto_now_add=True)
    
    class Meta:
        verbose_name = _("notification")
        verbose_name_plural = _("notifications")
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["recipient", "is_read"]),
            models.Index(fields=["created_at"]),
        ]
    
    def __str__(self):
        return f"Notification for {self.recipient.email} - {self.notification_type}"


class ModeratorAction(models.Model):
    """Moderator action log model."""
    
    class ActionType(models.TextChoices):
        EDIT = "edit", _("Edit")
        DELETE = "delete", _("Delete")
        LOCK = "lock", _("Lock Thread")
        UNLOCK = "unlock", _("Unlock Thread")
        PIN = "pin", _("Pin Thread")
        UNPIN = "unpin", _("Unpin Thread")
        APPROVE = "approve", _("Approve Content")
        REJECT = "reject", _("Reject Content")
        BAN_USER = "ban_user", _("Ban User")
        UNBAN_USER = "unban_user", _("Unban User")
    
    moderator = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name="moderator_actions"
    )
    action_type = models.CharField(
        max_length=20,
        choices=ActionType.choices
    )
    
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey("content_type", "object_id")
    
    reason = models.TextField(_("reason"), blank=True)
    created_at = models.DateTimeField(_("created at"), auto_now_add=True)
    
    class Meta:
        verbose_name = _("moderator action")
        verbose_name_plural = _("moderator actions")
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["moderator"]),
            models.Index(fields=["action_type"]),
        ]
    
    def __str__(self):
        return f"{self.action_type} by {self.moderator.email if self.moderator else 'System'}"


class UserBan(models.Model):
    """User ban model."""
    
    class BanType(models.TextChoices):
        TEMPORARY = "temporary", _("Temporary")
        PERMANENT = "permanent", _("Permanent")
    
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="bans"
    )
    banned_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name="bans_issued"
    )
    reason = models.TextField(_("reason"))
    ban_type = models.CharField(
        max_length=20,
        choices=BanType.choices,
        default=BanType.TEMPORARY
    )
    
    start_date = models.DateTimeField(_("start date"), auto_now_add=True)
    end_date = models.DateTimeField(_("end date"), null=True, blank=True)
    is_active = models.BooleanField(_("active"), default=True)
    
    created_at = models.DateTimeField(_("created at"), auto_now_add=True)
    
    class Meta:
        verbose_name = _("user ban")
        verbose_name_plural = _("user bans")
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["user", "is_active"]),
        ]
    
    def __str__(self):
        return f"Ban for {self.user.email} - {self.ban_type}"
    
    def is_currently_active(self):
        """Check if ban is currently active."""
        if not self.is_active:
            return False
        if self.ban_type == self.BanType.PERMANENT:
            return True
        if self.end_date and self.end_date < timezone.now():
            return False
        return True