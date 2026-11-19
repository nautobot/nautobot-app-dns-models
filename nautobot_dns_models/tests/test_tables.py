"""Unit tests for tables."""

from django.urls import reverse
from nautobot.apps.testing import TestCase

from nautobot_dns_models.choices import DNSZoneTypeChoices
from nautobot_dns_models.models import DNSZone
from nautobot_dns_models.tables import CatalogMemberZoneTable
from nautobot_dns_models.tests.fixtures import create_zone


class CatalogMemberZoneTableTestCase(TestCase):
    """Tests for the table of member zones on a catalog zone's detail page."""

    @classmethod
    def setUpTestData(cls):
        cls.catalog_zone = create_zone("catalog.example", type=DNSZoneTypeChoices.TYPE_CATALOG)
        cls.member_zone = create_zone("member.example", catalog_zone=cls.catalog_zone)

    def test_the_table_offers_no_catalog_actions_without_a_user(self):
        """A member zone table built without a user offers no catalog actions.

        Without a user, the table cannot tell which actions are permitted.
        """
        table = CatalogMemberZoneTable(DNSZone.objects.filter(pk=self.member_zone.pk))
        url = reverse("plugins:nautobot_dns_models:dnszone_remove_from_catalog", kwargs={"pk": self.member_zone.pk})
        self.assertNotIn(url, table.rows[0].get_cell("actions"))  # pylint: disable=no-member
