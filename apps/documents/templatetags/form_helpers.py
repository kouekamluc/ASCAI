"""
Template tags for form helpers to ensure unique IDs.
"""
from django import template

register = template.Library()


@register.filter
def unique_id(form_field, prefix=''):
    """
    Generate a unique ID for a form field.
    Usage: {{ form.field|unique_id:"prefix_" }}
    """
    if not form_field:
        return ''
    
    # Get the base ID from the field
    base_id = form_field.id_for_label
    
    # If prefix is provided, prepend it
    if prefix:
        return f"{prefix}_{base_id}"
    
    # If form has a prefix, use it
    if hasattr(form_field, 'form') and hasattr(form_field.form, 'prefix') and form_field.form.prefix:
        return f"{form_field.form.prefix}_{base_id}"
    
    return base_id


@register.simple_tag
def form_field_id(form_field, prefix=''):
    """
    Generate a unique ID for a form field (simple tag version).
    Usage: {% form_field_id form.field "prefix" as field_id %}
    """
    if not form_field:
        return ''
    
    base_id = form_field.id_for_label
    
    if prefix:
        return f"{prefix}_{base_id}"
    
    if hasattr(form_field, 'form') and hasattr(form_field.form, 'prefix') and form_field.form.prefix:
        return f"{form_field.form.prefix}_{base_id}"
    
    return base_id

