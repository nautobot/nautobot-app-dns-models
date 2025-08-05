"""Create fixtures for tests."""

from nautobot_dns_models.models import DNSZone


def create_dnszonemodel():
    """Fixture to create necessary number of DnsZoneModel for tests."""
    DNSZone.objects.create(name="Test One")
    DNSZone.objects.create(name="Test Two")
    DNSZone.objects.create(name="Test Three")
