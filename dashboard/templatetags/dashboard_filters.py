# dashboard/templatetags/dashboard_filters.py
from django import template

register = template.Library()


@register.filter
def format_duration(seconds):
    """Format seconds into a human-readable duration (min:sec)"""
    if seconds is None:
        return '-'

    minutes = int(seconds // 60)
    remaining_seconds = int(seconds % 60)

    if minutes > 0:
        return f"{minutes} min {remaining_seconds} sec"
    else:
        return f"{seconds:.1f} sec"