from django import template

register = template.Library()

@register.filter
def get(dictionary, key):
    """
    Template filter to get a value from a dictionary using a variable key.
    Usage: {{ my_dict|get:my_key }}
    """
    return dictionary.get(key, '')