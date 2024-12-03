"""Create fixtures for tests."""

from dns_models.models import DnsZoneModel


def create_dnszonemodel():
    """Fixture to create necessary number of DnsZoneModel for tests."""
    DnsZoneModel.objects.create(name="Test One")
    DnsZoneModel.objects.create(name="Test Two")
    DnsZoneModel.objects.create(name="Test Three")
