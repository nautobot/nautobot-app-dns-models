"""Unit tests for nautobot_dns_models."""

from nautobot.core.testing import APIViewTestCases

from nautobot_dns_models import models
from nautobot_dns_models.tests import fixtures


class DNSZoneModelAPIViewTest(APIViewTestCases.APIViewTestCase):
    # pylint: disable=too-many-ancestors
    """Test the API viewsets for DnsZoneModel."""

    model = models.DNSZoneModel
    create_data = [
        {
            "name": "Test Model 1",
        },
        {
            "name": "Test Model 2",
        },
    ]
    bulk_update_data = {"description": "Test Bulk Update"}
    brief_fields = ["created", "description", "display", "id", "last_updated", "name", "url"]

    @classmethod
    def setUpTestData(cls):
        fixtures.create_dnszonemodel()
