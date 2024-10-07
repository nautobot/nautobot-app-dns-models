"""DNS template tags."""

from django import template
from django.urls import reverse

# from django.utils.safestring import mark_safe
from django_jinja import library
from nautobot.core.utils import lookup

# HTML_NONE = mark_safe('<span class="text-muted">&mdash;</span>')  # noqa: S308
HTML_NONE = '<span class="text-muted">&mdash;</span>'

register = template.Library()


@library.filter()
@register.filter()
def url_with_action(value, action):
    """Return URL of a model based on the action.

    Args:
        value (obj): Object of a Model
        action (str): Necessary action (eg. edit)

    Returns:
        str: String URL of the specific object's action
    """
    if value is None:
        return HTML_NONE
    return reverse(lookup.get_route_for_model(value, action), args=[value.pk])


@library.filter()
@register.filter()
def user_has_change_access(user, instance):
    """Return URL of a model based on the action.

    Args:
        user (obj): Object of a User
        instance (obj): Instance of a Model

    Returns:
        bool: Returns true/false based on user's change permissions.
    """
    if user is None:
        return HTML_NONE
    return user.has_perm(f"nautobot_dns_models.change_{instance._meta.model_name}")


@library.filter()
@register.filter()
def user_has_delete_access(user, instance):
    """Return URL of a model based on the action.

    Args:
        user (obj): Object of a User
        instance (obj): a Model instance

    Returns:
        bool: Returns true/false based on user's delete permissions.
    """
    if user is None:
        return HTML_NONE
    return user.has_perm(f"nautobot_dns_models.delete_{instance._meta.model_name}")
