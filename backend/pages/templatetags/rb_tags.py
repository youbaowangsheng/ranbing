"""Custom template tags for Ranbing pages."""
from django import template

register = template.Library()

@register.filter
def get_item(dictionary, key):
    """{{ my_dict|get_item:key }} — dictionary lookup."""
    if dictionary is None:
        return None
    return dictionary.get(key)

@register.filter
def initials(name):
    """{{ name|initials }} — first character."""
    return str(name)[0:1] if name else '?'

@register.filter
def avatar_color(name):
    """{{ name|avatar_color }} — gradient string."""
    colors = [
        'linear-gradient(135deg,#e86a3a,#f0a06a)',
        'linear-gradient(135deg,#7c3aed,#a855f7)',
        'linear-gradient(135deg,#059669,#34d399)',
        'linear-gradient(135deg,#1a3a5c,#2d5a8a)',
    ]
    idx = (ord(str(name)[0:1]) if name else 0) % len(colors)
    return colors[idx]
