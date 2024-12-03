"""Unit tests for dns_models."""

from nautobot.apps.testing import APIViewTestCases

from nautobot_dns_models import models
from nautobot_dns_models.tests import fixtures


class DnsZoneModelAPIViewTest(APIViewTestCases.APIViewTestCase):
    # pylint: disable=too-many-ancestors
    """Test the API viewsets for DnsZoneModel."""

    model = models.DnsZoneModel
    create_data = [
        {
            "name": "Test Model 1",
            "description": "test description",
        },
        {
            "name": "Test Model 2",
        },
    ]
    bulk_update_data = {"description": "Test Bulk Update"}

    @classmethod
    def setUpTestData(cls):
        fixtures.create_dnszonemodel()
