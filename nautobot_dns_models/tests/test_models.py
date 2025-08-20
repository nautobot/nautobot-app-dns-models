"""Test DNSZone."""

from nautobot.apps.testing import ModelTestCases

from nautobot_dns_models import models
from nautobot_dns_models.tests import fixtures


class TestDNSZone(ModelTestCases.BaseModelTestCase):
    """Test DNSZone."""

    model = models.DNSZone

    @classmethod
    def setUpTestData(cls):
        """Create test data for DNSZone Model."""
        super().setUpTestData()
        # Create 3 objects for the model test cases.
        fixtures.create_dnszone()

    def test_create_dnszone_only_required(self):
        """Create with only required fields, and validate null description and __str__."""
        dnszone = models.DNSZone.objects.create(name="Development")
        self.assertEqual(dnszone.name, "Development")
        self.assertEqual(dnszone.description, "")
        self.assertEqual(str(dnszone), "Development")

    def test_create_dnszone_all_fields_success(self):
        """Create DNSZone with all fields."""
        dnszone = models.DNSZone.objects.create(name="Development", description="Development Test")
        self.assertEqual(dnszone.name, "Development")
        self.assertEqual(dnszone.description, "Development Test")
