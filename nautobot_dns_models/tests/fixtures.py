"""Create fixtures for tests."""

from nautobot_dns_models.models import DNSZone


def create_dnszone():
    """Fixture to create necessary number of DNSZone for tests."""
    DNSZone.objects.create(name="Test One")
    DNSZone.objects.create(name="Test Two")
    DNSZone.objects.create(name="Test Three")
