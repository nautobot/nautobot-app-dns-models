"""Unit tests for nautobot_dns_models."""

from nautobot.apps.testing import APIViewTestCases

from nautobot_dns_models import models
from nautobot_dns_models.models import (
    DNSZoneModel,
    SRVRecordModel,
)
from nautobot_dns_models.tests import fixtures


class DnsZoneModelAPIViewTest(APIViewTestCases.APIViewTestCase):
    # pylint: disable=too-many-ancestors
    """Test the API viewsets for DnsZoneModel."""

    model = models.DnsZoneModel
    # Any choice fields will require the choices_fields to be set
    # to the field names in the model that are choice fields.
    choices_fields = ()

    @classmethod
    def setUpTestData(cls):
        """Create test data for DnsZoneModel API viewset."""
        super().setUpTestData()
        # Create 3 objects for the generic API test cases.
        fixtures.create_dnszonemodel()
        # Create 3 objects for the api test cases.
        cls.create_data = [
            {
                "name": "API Test One",
                "description": "Test One Description",
            },
            {
                "name": "API Test Two",
                "description": "Test Two Description",
            },
            {
                "name": "API Test Three",
                "description": "Test Three Description",
            },
        ]
        cls.update_data = {
            "name": "Update Test Two",
            "description": "Test Two Description",
        }
        cls.bulk_update_data = {
            "description": "Test Bulk Update Description",
        }


class SRVRecordModelAPITestCase(APIViewTestCases.APIViewTestCase):
    """Test the Nautobot SRVRecordModel API."""

    model = models.SRVRecordModel
    view_namespace = "plugins-api:nautobot_dns_models"
    bulk_update_data = {
        "description": "Example bulk description",
    }
    brief_fields = [
        "name",
        "target",
    ]

    @classmethod
    def setUpTestData(cls):
        zone = DNSZoneModel.objects.create(name="example.com")
        SRVRecordModel.objects.create(
            name="_sip._tcp.example.com", priority=10, weight=5, port=5060, target="sip.example.com", zone=zone
        )
        SRVRecordModel.objects.create(
            name="_ldap._tcp.example.com", priority=20, weight=10, port=389, target="ldap.example.com", zone=zone
        )
        SRVRecordModel.objects.create(
            name="_xmpp._tcp.example.com", priority=30, weight=15, port=5222, target="xmpp.example.com", zone=zone
        )

        cls.create_data = [
            {
                "name": "_smtp._tcp.example.com",
                "priority": 40,
                "weight": 20,
                "port": 25,
                "target": "smtp.example.com",
                "zone": zone.id,
            },
            {
                "name": "_imap._tcp.example.com",
                "priority": 50,
                "weight": 25,
                "port": 143,
                "target": "imap.example.com",
                "zone": zone.id,
            },
            {
                "name": "_pop3._tcp.example.com",
                "priority": 60,
                "weight": 30,
                "port": 110,
                "target": "pop3.example.com",
                "zone": zone.id,
            },
        ]
