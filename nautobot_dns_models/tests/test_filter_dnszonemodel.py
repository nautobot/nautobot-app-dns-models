"""Test DnsZoneModel Filter."""

from django.test import TestCase
from nautobot_dns_models import filters
from nautobot_dns_models import models
from nautobot_dns_models.tests import fixtures


class DnsZoneModelFilterTestCase(TestCase):
    """DnsZoneModel Filter Test Case."""

    queryset = models.DnsZoneModel.objects.all()
    filterset = filters.DnsZoneModelFilterSet

    @classmethod
    def setUpTestData(cls):
        """Setup test data for DnsZoneModel Model."""
        fixtures.create_dnszonemodel()

    def test_q_search_name(self):
        """Test using Q search with name of DnsZoneModel."""
        params = {"q": "Test One"}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 1)

    def test_q_search_slug(self):
        """Test using Q search with slug of DnsZoneModel."""
        params = {"q": "test-one"}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 1)

    def test_q_invalid(self):
        """Test using invalid Q search for DnsZoneModel."""
        params = {"q": "test-five"}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 0)
