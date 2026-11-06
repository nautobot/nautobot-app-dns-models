"""Signal handlers for nautobot_dns_models."""

from django.db.models import Q
from django.db.models.signals import post_delete
from django.dispatch import receiver

from nautobot_dns_models.models import DNSZone
from nautobot_dns_models.utils import dns_name_key


@receiver(post_delete, sender=DNSZone)
def reparent_children_of_deleted_zone(sender, instance, **kwargs):  # pylint: disable=unused-argument
    """Move the children of a deleted zone to the zone that now encloses them.

    `on_delete=SET_NULL` clears their parent first. A signal rather than `DNSZone.delete()` also covers
    `QuerySet.delete()`, which Nautobot's bulk delete uses.
    """
    key = dns_name_key(instance.name)
    orphans = DNSZone.objects.filter(dns_view_id=instance.dns_view_id, parent__isnull=True)
    if key:
        orphans = orphans.filter(Q(name__iendswith=f".{key}") | Q(name__iendswith=f".{key}."))
    new_parent = DNSZone.get_enclosing_zone(instance.name, instance.dns_view_id)
    if new_parent is not None:
        orphans.update(parent=new_parent)
