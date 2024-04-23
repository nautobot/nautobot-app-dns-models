"""Create fixtures for tests."""

from nautobot_dns_models.models import DnsZoneModel


def create_dnszonemodel():
    """Fixture to create necessary number of DnsZoneModel for tests."""
    DnsZoneModel.objects.create(name="Test One", slug="test-one")
    DnsZoneModel.objects.create(name="Test Two", slug="test-two")
    DnsZoneModel.objects.create(name="Test Three", slug="test-three")
