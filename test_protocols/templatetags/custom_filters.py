from django import template
from django.db.models import QuerySet

register = template.Library()


@register.filter
def get(dictionary, key):
    """
    Template filter to get a value from a dictionary using a variable key.
    Usage: {{ my_dict|get:my_key }}
    """
    return dictionary.get(key, '')


@register.filter
def get_item(dictionary, key):
    """Get an item from a dictionary using the key"""
    return dictionary.get(key)


@register.filter
def regroup_by(queryset, related_field):
    """
    Collects all related objects from a queryset based on a related field.

    For example, with steps and verification_methods:
    {% with verifications=protocol.steps.all|regroup_by:"verification_methods" %}

    This will collect all verification methods related to all steps.
    """
    if not queryset:
        return []

    result = []
    seen_ids = set()

    for item in queryset:
        related_manager = getattr(item, related_field, None)
        if related_manager is None:
            continue

        if isinstance(related_manager, QuerySet):
            related_items = related_manager
        else:
            # It's a RelatedManager
            related_items = related_manager.all()

        for related_item in related_items:
            if related_item.id not in seen_ids:
                seen_ids.add(related_item.id)
                result.append(related_item)

    return result


@register.filter
def remainder(value, arg):
    """
    Returns the remainder of dividing the value by the argument.
    Usage: {{ value|remainder:arg }}

    Example: {{ 5|remainder:2 }} returns 1
    """
    try:
        return float(value) % float(arg)
    except (ValueError, TypeError):
        return 0


@register.filter
def divisibleby(value, arg):
    """
    Returns the integer division of the value by the argument.
    Usage: {{ value|divisibleby:arg }}

    Example: {{ 5|divisibleby:2 }} returns 2
    """
    try:
        return int(float(value) // float(arg))
    except (ValueError, TypeError):
        return 0