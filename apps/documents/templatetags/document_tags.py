"""
Template tags for document permissions.
"""

from django import template

register = template.Library()


@register.filter
def can_view(document, user):
    """Check if user can view the document."""
    return document.can_view(user)


@register.filter
def can_download(document, user):
    """Check if user can download the document."""
    return document.can_download(user)


@register.filter
def can_edit(document, user):
    """Check if user can edit the document."""
    return document.can_edit(user)


@register.filter
def can_delete(document, user):
    """Check if user can delete the document."""
    return document.can_delete(user)










