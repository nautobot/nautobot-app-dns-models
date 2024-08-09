"""Create fixtures for tests."""

from nautobot_dns_models.models import DNSZoneModel


def create_dnszonemodel():
    """Fixture to create necessary number of DnsZoneModel for tests."""
    DNSZoneModel.objects.create(name="Test One")
    DNSZoneModel.objects.create(name="Test Two")
    DNSZoneModel.objects.create(name="Test Three")
