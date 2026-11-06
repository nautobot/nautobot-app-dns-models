"""DNS name helpers for nautobot_dns_models.

These functions are pure (no ORM access) so that data migrations can use them as well as the models.
"""

from collections.abc import Iterable, Iterator


def dns_name_key(name: str) -> str:
    """Return `name` in the form used to compare DNS names.

    Names compare case-insensitively (RFC 4343 §2) and an absolute name's trailing root dot is ignored. The root
    name itself (`.`) becomes the empty string.
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


def ancestor_keys(name_key: str) -> Iterator[str]:
    """Yield the keys of every name above `name_key`, most specific first, ending with the root (`""`).

    `a.example.com` yields `example.com`, `com`, then `""`.
    """
    if name_key == "":
        return
    labels = name_key.split(".")
    for index in range(1, len(labels)):
        yield ".".join(labels[index:])
    yield ""


def compute_zone_parents(zones: Iterable[tuple]) -> dict:
    """Map each zone's primary key to the primary key of its most specific enclosing zone, or `None`.

    Args:
        zones: `(pk, name, dns_view_id)` tuples. Zones only enclose zones in the same DNS view.
    """
    zone_list = list(zones)
    pks_by_view = {}
    for pk, name, dns_view_id in zone_list:
        pks_by_view.setdefault(dns_view_id, {}).setdefault(dns_name_key(name), pk)

    parents = {}
    for pk, name, dns_view_id in zone_list:
        view_pks = pks_by_view[dns_view_id]
        parents[pk] = next((view_pks[key] for key in ancestor_keys(dns_name_key(name)) if key in view_pks), None)
    return parents
