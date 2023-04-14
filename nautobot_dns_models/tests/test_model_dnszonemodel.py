"""Test DnsZoneModel."""

from django.test import TestCase

from nautobot_dns_models import models


class TestDnsZoneModel(TestCase):
    """Test DnsZoneModel."""

    def test_create_dnszonemodel_only_required(self):
        """Create with only required fields, and validate null description and __str__."""
        dnszonemodel = models.DnsZoneModel.objects.create(name="Development", slug="development")
        self.assertEqual(dnszonemodel.name, "Development")
        self.assertEqual(dnszonemodel.description, "")
        self.assertEqual(str(dnszonemodel), "Development")
        self.assertEqual(dnszonemodel.slug, "development")

    def test_create_dnszonemodel_all_fields_success(self):
        """Create DnsZoneModel with all fields."""
        dnszonemodel = models.DnsZoneModel.objects.create(
            name="Development", slug="development", description="Development Test"
        )
        self.assertEqual(dnszonemodel.name, "Development")
        self.assertEqual(dnszonemodel.slug, "development")
        self.assertEqual(dnszonemodel.description, "Development Test")
