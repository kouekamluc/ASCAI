"""
Audit logging signals for ASCAI platform.
"""
from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver
from django.contrib.contenttypes.models import ContentType
from .models import AuditLog


def get_model_fields_dict(instance):
    """Get dictionary of model fields and values."""
    fields = {}
    for field in instance._meta.get_fields():
        if hasattr(instance, field.name):
            try:
                value = getattr(instance, field.name)
                # Convert to serializable format
                if hasattr(value, 'pk'):
                    fields[field.name] = value.pk
                elif hasattr(value, '__str__'):
                    fields[field.name] = str(value)
                else:
                    fields[field.name] = value
            except Exception:
                pass
    return fields


@receiver(post_save)
def log_model_change(sender, instance, created, **kwargs):
    """Log model changes to audit log."""
    # Skip audit log model itself to avoid recursion
    if sender == AuditLog:
        return
    
    # Only log changes to specific models
    tracked_models = [
        'Member',
        'Payment',
        'MemberApplication',
        'Event',
        'EventRegistration',
    ]
    
    if sender.__name__ not in tracked_models:
        return
    
    # Get user from request if available
    user = None
    ip_address = None
    user_agent = None
    
    # Try to get request from thread-local storage (if available)
    try:
        from django.contrib.auth import get_user
        from django.utils.functional import SimpleLazyObject
        from threading import local
        
        # This is a simplified approach - in production, use middleware
        # to store request in thread-local storage
        pass
    except Exception:
        pass
    
    action = AuditLog.ActionType.CREATE if created else AuditLog.ActionType.UPDATE
    
    # Get old value for updates
    old_value = None
    if not created and hasattr(instance, '_old_state'):
        old_value = instance._old_state
    
    # Get new value
    new_value = get_model_fields_dict(instance)
    
    # Create audit log entry
    try:
        AuditLog.objects.create(
            content_type=ContentType.objects.get_for_model(instance),
            object_id=instance.pk,
            action=action,
            changed_by=user,
            old_value=old_value,
            new_value=new_value,
            ip_address=ip_address,
            user_agent=user_agent,
        )
    except Exception:
        # Silently fail if audit logging fails
        pass


@receiver(pre_delete)
def log_model_deletion(sender, instance, **kwargs):
    """Log model deletions to audit log."""
    if sender == AuditLog:
        return
    
    tracked_models = [
        'Member',
        'Payment',
        'MemberApplication',
    ]
    
    if sender.__name__ not in tracked_models:
        return
    
    old_value = get_model_fields_dict(instance)
    
    try:
        AuditLog.objects.create(
            content_type=ContentType.objects.get_for_model(instance),
            object_id=instance.pk,
            action=AuditLog.ActionType.DELETE,
            changed_by=None,  # User info not available in pre_delete
            old_value=old_value,
            new_value=None,
        )
    except Exception:
        pass

