"""
Signals for forums app.
"""

from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver
from django.contrib.contenttypes.models import ContentType
from django.utils.translation import gettext_lazy as _
from .models import Thread, Reply, Notification, Vote
from django.core.mail import send_mail
from django.conf import settings
import re


def extract_mentions(text):
    """Extract @mentions from text."""
    if not text:
        return []
    mentions = re.findall(r'@(\w+)', text)
    return mentions


@receiver(post_save, sender=Reply)
def create_reply_notification(sender, instance, created, **kwargs):
    """Create notification when a reply is created."""
    if not created or not instance.is_approved:
        return
    
    # Don't notify if replying to own thread
    if instance.author == instance.thread.author:
        return
    
    # Create notification for thread author
    Notification.objects.create(
        recipient=instance.thread.author,
        notification_type=Notification.NotificationType.REPLY,
        content_type=ContentType.objects.get_for_model(Reply),
        object_id=instance.pk,
        message=_("%(user)s replied to your thread \"%(thread)s\"") % {
            "user": instance.author.full_name,
            "thread": instance.thread.title
        }
    )
    
    # Send email notification
    try:
        from django.template.loader import render_to_string
        from django.contrib.sites.models import Site
        
        site = Site.objects.get_current()
        protocol = "https" if not settings.DEBUG else "http"
        thread_url = f"{protocol}://{site.domain}{instance.thread.get_absolute_url()}"
        
        context = {
            "recipient": instance.thread.author,
            "thread": instance.thread,
            "reply": instance,
            "thread_url": thread_url,
        }
        
        html_message = render_to_string("forums/emails/reply_notification.html", context)
        plain_message = _("You received a new reply to your thread \"%(thread)s\" from %(user)s.\n\n%(content)s\n\nView: %(url)s") % {
            "thread": instance.thread.title,
            "user": instance.author.full_name,
            "content": instance.content[:500],
            "url": thread_url
        }
        
        send_mail(
            subject=_("New Reply to Your Thread: %(thread)s") % {"thread": instance.thread.title},
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[instance.thread.author.email],
            html_message=html_message,
            fail_silently=True,
        )
        # Mark notification as emailed
        notification = Notification.objects.filter(
            recipient=instance.thread.author,
            notification_type=Notification.NotificationType.REPLY,
            content_type=ContentType.objects.get_for_model(Reply),
            object_id=instance.pk
        ).first()
        if notification:
            notification.is_emailed = True
            notification.save()
    except Exception:
        # Email sending failed, continue silently
        pass
    
    # Check for mentions in reply content
    mentions = extract_mentions(instance.content)
    from django.contrib.auth import get_user_model
    User = get_user_model()
    
    for mention in mentions:
        try:
            # Try to find user by email or username
            mentioned_user = User.objects.filter(email__icontains=mention).first()
            if mentioned_user and mentioned_user != instance.author:
                Notification.objects.create(
                    recipient=mentioned_user,
                    notification_type=Notification.NotificationType.MENTION,
                    content_type=ContentType.objects.get_for_model(Reply),
                    object_id=instance.pk,
                    message=_("%(user)s mentioned you in a reply") % {
                        "user": instance.author.full_name
                    }
                )
        except Exception:
            # Skip if user not found
            pass


@receiver(post_save, sender=Thread)
def update_thread_statistics(sender, instance, created, **kwargs):
    """Update thread statistics when needed."""
    # Only update reply count if this is a new thread
    # Skip if update_fields contains reply_count to avoid recursion
    update_fields = kwargs.get('update_fields')
    if update_fields and 'reply_count' in update_fields:
        return  # Skip to avoid recursion
    # For new threads, set initial reply count (will be 0)
    # For existing threads, this should be handled by Reply.save() signal
    if created:
        instance.update_reply_count()


@receiver(post_save, sender=Reply)
def update_thread_on_reply(sender, instance, created, **kwargs):
    """Update thread when reply is created/updated."""
    if created and instance.is_approved:
        instance.thread.update_reply_count()
        instance.thread.update_last_activity()


@receiver(post_save, sender=Vote)
def create_vote_notification(sender, instance, created, **kwargs):
    """Create notification when content is voted on (optional)."""
    # Only notify on upvotes and only for significant content
    if not created or instance.vote_type != Vote.VoteType.UPVOTE:
        return
    
    # Determine content type
    obj = instance.content_object
    if not obj:
        return
    
    # Get author based on content type
    if isinstance(obj, Thread):
        content_author = obj.author
    elif isinstance(obj, Reply):
        content_author = obj.author
    else:
        return
    
    # Don't notify if voting on own content
    if instance.user == content_author:
        return
    
    # Only notify for significant votes (e.g., 10+ upvotes)
    vote_count = Vote.objects.filter(
        content_type=instance.content_type,
        object_id=instance.object_id,
        vote_type=Vote.VoteType.UPVOTE
    ).count()
    
    if vote_count >= 10:
        Notification.objects.create(
            recipient=content_author,
            notification_type=Notification.NotificationType.VOTE,
            content_type=instance.content_type,
            object_id=instance.object_id,
            message=_("Your post reached %(count)s upvotes!") % {"count": vote_count}
        )


# Signal for Celery tasks (when implemented)
# @shared_task
# def send_notification_email_async(notification_id):
#     """Async task to send notification emails."""
#     try:
#         notification = Notification.objects.get(pk=notification_id)
#         # Send email logic here
#         notification.is_emailed = True
#         notification.save()
#     except Notification.DoesNotExist:
#         pass

