"""DNS template tags."""

from django import template
from django.urls import NoReverseMatch, reverse
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from django_jinja import library

from nautobot.core.utils import lookup

HTML_NONE = mark_safe('<span class="text-muted">&mdash;</span>')  # noqa: S308

register = template.Library()


@library.filter()
@register.filter()
def url_with_action(value, action):
    """Return URL of a model based on the action.

    Args:
        value (obj): Object of a Model
        action (str): Necessary action (eg. edit)

    Returns:
        _type_: String URL of the specific object's action
    """
    if value is None:
        return HTML_NONE
    return reverse(lookup.get_route_for_model(value, action), args=[value.pk])
