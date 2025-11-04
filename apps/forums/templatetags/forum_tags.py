"""
Custom template tags for forums app.
"""

from django import template
from django.contrib.contenttypes.models import ContentType

register = template.Library()


@register.filter
def get_item(dictionary, key):
    """Get an item from a dictionary by key."""
    if dictionary is None:
        return None
    return dictionary.get(key)


@register.filter
def content_type_id(obj):
    """Get content type ID for an object."""
    if obj is None:
        return None
    content_type = ContentType.objects.get_for_model(obj.__class__)
    return content_type.pk






