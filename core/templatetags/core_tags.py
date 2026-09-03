"""Custom template tags and filters for the core app."""
from django import template

register = template.Library()


@register.filter(name="dict_get")
def dict_get(dictionary, key):
    """
    Template filter to access a dictionary value by key (integer or string).
    Usage: {{ my_dict|dict_get:key }}
    Required by the timetable grid template to access day-keyed data.
    """
    if isinstance(dictionary, dict):
        return dictionary.get(key, [])
    return []
