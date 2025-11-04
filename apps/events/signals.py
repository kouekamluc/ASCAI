"""
Signals for events app.
"""

from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from .models import Event


@receiver(pre_save, sender=Event)
def event_pre_save(sender, instance, **kwargs):
    """Store original event data before save."""
    if instance.pk:
        try:
            original = Event.objects.get(pk=instance.pk)
            instance._original_start_date = original.start_date
            instance._original_location = original.location
            instance._original_title = original.title
        except Event.DoesNotExist:
            instance._original_start_date = None
            instance._original_location = None
            instance._original_title = None
    else:
        instance._original_start_date = None
        instance._original_location = None
        instance._original_title = None


@receiver(post_save, sender=Event)
def event_post_save(sender, instance, created, **kwargs):
    """Send update notifications when event is modified."""
    if not created and instance.is_published:
        # Check if important fields changed
        changed = False
        if hasattr(instance, '_original_start_date'):
            if (instance._original_start_date and 
                instance._original_start_date != instance.start_date):
                changed = True
            if (instance._original_location and 
                instance._original_location != instance.location):
                changed = True
            if (instance._original_title and 
                instance._original_title != instance.title):
                changed = True
        
        if changed:
            # Send update notifications (async via Celery, with fallback to sync)
            from .tasks import send_event_update_notification
            from .utils import safe_task_execute
            safe_task_execute(send_event_update_notification, instance.id)

