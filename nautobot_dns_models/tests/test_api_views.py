"""Unit tests for nautobot_dns_models."""

from nautobot.core.testing import APIViewTestCases

from nautobot_dns_models import models
from nautobot_dns_models.tests import fixtures


class DnsZoneModelAPIViewTest(APIViewTestCases.APIViewTestCase):
    # pylint: disable=too-many-ancestors
    """Test the API viewsets for DnsZoneModel."""

    model = models.DnsZoneModel
    create_data = [
        {
            "name": "Test Model 1",
            "slug": "test-model-1",
        },
        {
            "name": "Test Model 2",
            "slug": "test-model-2",
        },
    ]
    bulk_update_data = {"description": "Test Bulk Update"}
    brief_fields = ["created", "description", "display", "id", "last_updated", "name", "slug", "url"]

    @classmethod
    def setUpTestData(cls):
        fixtures.create_dnszonemodel()
