"""Unit tests for views."""

from nautobot.apps.testing import ViewTestCases

from nautobot_dns_models import models
from nautobot_dns_models.tests import fixtures


class DnsZoneModelViewTest(ViewTestCases.PrimaryObjectViewTestCase):
    # pylint: disable=too-many-ancestors
    """Test the DnsZoneModel views."""

    model = models.DnsZoneModel
    bulk_edit_data = {"description": "Bulk edit views"}
    form_data = {
        "name": "Test 1",
        "description": "Initial model",
    }
    csv_data = (
        "name",
        "Test csv1",
        "Test csv2",
        "Test csv3",
    )

    @classmethod
    def setUpTestData(cls):
        fixtures.create_dnszonemodel()
