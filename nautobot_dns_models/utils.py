"""Utility functions for Nautobot DNS Models."""

from collections.abc import Iterable, Iterator

from django.db.models import Count
from django.db.models.functions import Lower


def ancestor_keys(name: str) -> Iterator[str]:
    """Yield every name above the lowercase name `name`, most specific first.

    `a.example.com` yields `example.com`, then `com`.
    """
    labels = name.split(".")
    for index in range(1, len(labels)):
        yield ".".join(labels[index:])


def compute_zone_parents(zones: Iterable[tuple]) -> dict:
    """Map each zone's primary key to the primary key of its most specific enclosing zone, or `None`.

    Names compare case-insensitively (RFC 4343 §2), as zone name uniqueness does.

    Args:
        zones: `(pk, name, dns_view_id)` tuples. Zones only enclose zones in the same DNS view.
    """
    zone_list = list(zones)
    pks_by_view = {}
    for pk, name, dns_view_id in zone_list:
        pks_by_view.setdefault(dns_view_id, {}).setdefault(name.lower(), pk)

    parents = {}
    for pk, name, dns_view_id in zone_list:
        view_pks = pks_by_view[dns_view_id]
        parents[pk] = next((view_pks[key] for key in ancestor_keys(name.lower()) if key in view_pks), None)
    return parents


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


def dns_name_key(name: str) -> str:
    """Return `name` in the form used to compare DNS names that may be written as absolute names.

    Names compare case-insensitively (RFC 4343 §2) and one trailing root dot is ignored, so NS record `server` values
    such as `ns1.example.com.` match `ns1.example.com`. The root name itself (`.`) becomes the empty string.
    """
    key = name.lower()
    if key.endswith("."):
        key = key[:-1]
    return key


def is_subdomain(name_key: str, ancestor_key: str) -> bool:
    """Return whether `name_key` lies strictly below `ancestor_key`; both are `dns_name_key()` values."""
    if name_key == ancestor_key:
        return False
    if ancestor_key == "":
        return True
    return name_key.endswith(f".{ancestor_key}")


def owner_fqdn(name: str, zone_name: str) -> str:
    """Return the fully qualified owner name of a record named `name` in zone `zone_name`, without a trailing dot.

    `@` and the empty string denote the zone apex.
    """
    zone = zone_name[:-1] if zone_name.endswith(".") else zone_name
    if name in ("", "@"):
        return zone or "."
    return f"{name}.{zone}" if zone else name


def relative_owner_name(fqdn_key: str, zone_key: str) -> str:
    """Return the owner name of `fqdn_key` relative to `zone_key` (`@` for the apex); both are `dns_name_key()` values.

    The caller must ensure the name is at or below the zone.
    """
    if fqdn_key == zone_key:
        return "@"
    if zone_key == "":
        return fqdn_key
    return fqdn_key[: -(len(zone_key) + 1)]
