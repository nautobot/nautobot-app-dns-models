"""Unit tests for views."""

from nautobot.core.testing import ViewTestCases

from nautobot_dns_models import models
from nautobot_dns_models.tests import fixtures


class DnsZoneModelViewTest(ViewTestCases.PrimaryObjectViewTestCase):
    # pylint: disable=too-many-ancestors
    """Test the DnsZoneModel views."""

    model = models.DNSZoneModel
    bulk_edit_data = {"description": "Bulk edit views"}
    form_data = {
        "name": "Test 1",
        "description": "Initial model",
    }

    @classmethod
    def setUpTestData(cls):
        fixtures.create_dnszonemodel()

    def test_bulk_import_objects_with_constrained_permission(self):
        """Auto-generated model does not implement `bulk_import`."""

    def test_bulk_import_objects_with_permission(self):
        """Auto-generated model does not implement `bulk_import`."""

    def test_bulk_import_objects_without_permission(self):
        """Auto-generated model does not implement `bulk_import`."""

    def test_bulk_import_objects_with_permission_csv_file(self):
        """Auto-generated model does not implement `bulk_import`."""

    def test_has_advanced_tab(self):
        """Auto-generated model does not implement an advanced tab."""
