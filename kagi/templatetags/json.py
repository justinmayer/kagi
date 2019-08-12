import json

from django import template
from django.utils.safestring import mark_safe

register = template.Library()


@register.filter(name="json", is_safe=True)
def json_filter(a):
    """
    Output the json encoding of its argument.
    This will escape all the HTML/XML special characters with their unicode
    escapes, so it is safe to be output anywhere except for inside a tag
    attribute.
    If the output needs to be put in an attribute, entitize the output of this
    filter.
    """
    json_str = json.dumps(a)

    # Escape all the XML/HTML special characters.
    escapes = ['<', '>', '&']
    for c in escapes:
        json_str = json_str.replace(c, r'\u%04x' % ord(c))

    # now it's safe to use mark_safe
    return mark_safe(json_str)
