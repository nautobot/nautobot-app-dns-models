"""Signal handlers for nautobot_dns_models."""

from django.db.models.signals import post_delete
from django.dispatch import receiver

from nautobot_dns_models.models import DNSZone, rebuild_zone_hierarchy


@receiver(post_delete, sender=DNSZone)
def reparent_zones_after_delete(sender, instance, **kwargs):  # pylint: disable=unused-argument
    """Recompute the parent of every zone in the deleted zone's DNS View.

    `on_delete=SET_NULL` clears the parent of the deleted zone's children first. A signal rather than
    `DNSZone.delete()` also covers `QuerySet.delete()`, which Nautobot's bulk delete uses.
    """
    rebuild_zone_hierarchy(dns_view=instance.dns_view_id)
