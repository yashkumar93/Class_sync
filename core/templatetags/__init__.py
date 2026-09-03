"""Custom template tags and filters for the core app."""
from django import template

register = template.Library()


@register.filter(name="dict_get")
def dict_get(dictionary, key):
    """
    Template filter to access a dictionary value by key.
    Usage: {{ my_dict|dict_get:key }}
    """
    if isinstance(dictionary, dict):
        return dictionary.get(key, [])
    return []
