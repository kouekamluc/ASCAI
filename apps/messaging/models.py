from django.db import models
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.core.cache import cache

User = get_user_model()


class Conversation(models.Model):
    """Represents a conversation between two users."""
    participants = models.ManyToManyField(
        User, related_name="conversations", verbose_name=_("Participants")
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Created at"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Updated at"))
    last_message = models.ForeignKey(
        'Message',
        null=True,
        blank=True,
        related_name='last_message_conversation',
        on_delete=models.SET_NULL,
        verbose_name=_("Last message")
    )

    class Meta:
        verbose_name = _("Conversation")
        verbose_name_plural = _("Conversations")
        ordering = ['-updated_at']

    def __str__(self):
        return f"Conversation {self.id}"

    def get_other_participant(self, user):
        """Get the other participant in the conversation."""
        return self.participants.exclude(id=user.id).first()

    def mark_as_read(self, user):
        """Mark all messages in this conversation as read for a user."""
        self.messages.exclude(sender=user).update(is_read=True)

    def get_unread_count(self, user):
        """Get unread message count for a user."""
        return self.messages.exclude(
            sender=user
        ).filter(
            is_read=False
        ).count()


class Message(models.Model):
    """Represents a message in a conversation."""
    conversation = models.ForeignKey(
        Conversation,
        on_delete=models.CASCADE,
        related_name='messages',
        verbose_name=_("Conversation")
    )
    sender = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='sent_messages',
        verbose_name=_("Sender")
    )
    content = models.TextField(verbose_name=_("Content"))
    is_read = models.BooleanField(default=False, verbose_name=_("Is read"))
    is_admin_message = models.BooleanField(
        default=False, 
        verbose_name=_("Is admin message"),
        help_text=_("Indicates if this message is from an admin or board member")
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Created at"))

    class Meta:
        verbose_name = _("Message")
        verbose_name_plural = _("Messages")
        ordering = ['created_at']

    def __str__(self):
        return f"Message from {self.sender.full_name} at {self.created_at}"

    def save(self, *args, **kwargs):
        # Automatically set is_admin_message if sender is admin or board member
        if not self.pk:  # Only on creation
            self.is_admin_message = self.sender.is_admin() or self.sender.is_board_member()
        super().save(*args, **kwargs)
        # Update conversation's last message (only if conversation exists and is saved)
        try:
            if self.conversation and self.conversation.pk:
                self.conversation.last_message = self
                self.conversation.save(update_fields=['last_message', 'updated_at'])
        except Exception as e:
            # Log but don't fail if conversation update fails
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"Failed to update conversation last_message: {e}")


class UserPresence(models.Model):
    """Track user online/offline presence."""
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='presence',
        verbose_name=_("User")
    )
    is_online = models.BooleanField(default=False, verbose_name=_("Is online"))
    last_seen = models.DateTimeField(auto_now=True, verbose_name=_("Last seen"))

    class Meta:
        verbose_name = _("User Presence")
        verbose_name_plural = _("User Presences")

    def __str__(self):
        return f"{self.user.full_name} - {'Online' if self.is_online else 'Offline'}"

    @classmethod
    def get_online_users(cls):
        """Get all currently online users."""
        return cls.objects.filter(is_online=True).select_related('user')

    @classmethod
    def update_presence(cls, user, is_online):
        """Update user's presence status."""
        presence, created = cls.objects.get_or_create(user=user)
        presence.is_online = is_online
        presence.save()
        return presence











