"""Helpers shared by the nautobot_dns_models test modules."""

from nautobot_dns_models.models import DNSZone


def create_zone(name, **kwargs):
    """Create a zone, supplying the fields the model requires but the test does not care about."""
    return DNSZone.objects.create(
        name=name,
        filename=f"{name}.zone",
        soa_mname=f"ns1.{name}.",
        soa_rname=f"admin@{name}",
        **kwargs,
    )
