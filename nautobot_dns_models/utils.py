"""Utility functions for Nautobot DNS Models."""

from django.db.models import Count
from django.db.models.functions import Lower


def get_dns_zone_name_collisions(dns_zone_model):
    """Return groups of DNS zones whose names differ only by letter case within the same DNS view.

    Args:
        dns_zone_model: The `DNSZone` model class.

    Returns:
        list[list]: One list of zones per collision, ordered by view name and then zone name.
    """
    zones = dns_zone_model.objects.annotate(name_lower=Lower("name"))
    collision_keys = (
        zones.values("dns_view", "name_lower")
        .order_by()
        .annotate(count=Count("pk"))
        .filter(count__gt=1)
        .values_list("dns_view", "name_lower")
    )
    collisions = []
    for dns_view, name_lower in collision_keys:
        collisions.append(
            list(zones.filter(dns_view=dns_view, name_lower=name_lower).select_related("dns_view").order_by("name"))
        )
    collisions.sort(key=lambda group: (group[0].dns_view.name, group[0].name.lower()))
    return collisions


def format_dns_zone_name_collisions(collisions, limit=None, record_counts=None):
    """Return a human-readable description of DNS zone name collisions.

    Args:
        collisions (list[list]): Groups of colliding zones, as returned by `get_dns_zone_name_collisions`.
        limit (int, optional): Maximum number of groups to describe; the remainder is summarized in one line.
        record_counts (dict, optional): Mapping of zone primary key to the number of records in the zone.

    Returns:
        str: The description, one line per group of colliding zones.
    """
    lines = [
        f"Found {len(collisions)} group(s) of DNS zones whose names differ only by letter case within the same DNS view.",
    ]
    for group in collisions if limit is None else collisions[:limit]:
        zone_descriptions = []
        for zone in group:
            description = f'"{zone.name}" (ID {zone.pk}'
            if record_counts is not None:
                description += f", {record_counts.get(zone.pk, 0)} record(s)"
            zone_descriptions.append(f"{description})")
        lines.append(f'    View "{group[0].dns_view.name}": {", ".join(zone_descriptions)}')
    if limit is not None and len(collisions) > limit:
        lines.append(f"    ...and {len(collisions) - limit} more.")
    return "\n".join(lines)
