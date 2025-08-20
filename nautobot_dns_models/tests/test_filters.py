"""Test DNSZone Filter."""

from nautobot.apps.testing import FilterTestCases

from nautobot_dns_models import filters, models
from nautobot_dns_models.tests import fixtures


class DNSZoneFilterTestCase(FilterTestCases.FilterTestCase):
    """DNSZone Filter Test Case."""

    queryset = models.DNSZone.objects.all()
    filterset = filters.DNSZoneFilterSet
    generic_filter_tests = (
        ("id",),
        ("created",),
        ("last_updated",),
        ("name",),
    )

    @classmethod
    def setUpTestData(cls):
        """Setup test data for DNSZone Model."""
        fixtures.create_dnszone()

    def test_q_search_name(self):
        """Test using Q search with name of DNSZone."""
        params = {"q": "Test One"}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 1)

    def test_q_invalid(self):
        """Test using invalid Q search for DNSZone."""
        params = {"q": "test-five"}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 0)
