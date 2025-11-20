"""
Signals for news app.
"""
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import NewsPost
from .tasks import send_news_notification


@receiver(post_save, sender=NewsPost)
def notify_on_news_publish(sender, instance, created, **kwargs):
    """Send notification when news is published."""
    # Only send notification if:
    # 1. News is being published (is_published changed to True)
    # 2. Or it's a new post that's immediately published
    if instance.is_published and instance.visibility == NewsPost.Visibility.PUBLIC:
        # Check if this is a new publication or update
        if created or (hasattr(instance, '_was_published') and not instance._was_published):
            # Send notification asynchronously via Celery
            try:
                send_news_notification.delay(instance.id)
            except Exception:
                # Fallback to synchronous if Celery is not available
                send_news_notification(instance.id)


@receiver(post_save, sender=NewsPost)
def track_published_state(sender, instance, **kwargs):
    """Track previous published state for signal logic."""
    if hasattr(instance, '_was_published'):
        instance._was_published = instance.is_published
    else:
        # Store initial state
        try:
            old_instance = NewsPost.objects.get(pk=instance.pk)
            instance._was_published = old_instance.is_published
        except NewsPost.DoesNotExist:
            instance._was_published = False

