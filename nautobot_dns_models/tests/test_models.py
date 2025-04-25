"""Test DnsZoneModel."""

from nautobot.apps.testing import ModelTestCases

from nautobot_dns_models import models
from nautobot_dns_models.tests import fixtures


class TestDnsZoneModel(ModelTestCases.BaseModelTestCase):
    """Test DnsZoneModel."""

    model = models.DnsZoneModel

    @classmethod
    def setUpTestData(cls):
        """Create test data for DnsZoneModel Model."""
        super().setUpTestData()
        # Create 3 objects for the model test cases.
        fixtures.create_dnszonemodel()

    def test_create_dnszonemodel_only_required(self):
        """Create with only required fields, and validate null description and __str__."""
        dnszonemodel = models.DnsZoneModel.objects.create(name="Development")
        self.assertEqual(dnszonemodel.name, "Development")
        self.assertEqual(dnszonemodel.description, "")
        self.assertEqual(str(dnszonemodel), "Development")

    def test_create_dnszonemodel_all_fields_success(self):
        """Create DnsZoneModel with all fields."""
        dnszonemodel = models.DnsZoneModel.objects.create(name="Development", description="Development Test")
        self.assertEqual(dnszonemodel.name, "Development")
        self.assertEqual(dnszonemodel.description, "Development Test")
