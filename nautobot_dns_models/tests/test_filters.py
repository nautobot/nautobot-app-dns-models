"""Test DnsZoneModel Filter."""

from nautobot.apps.testing import FilterTestCases, TestCase

from nautobot_dns_models import filters, models
from nautobot_dns_models.filters import (
    SRVRecordModelFilterSet,
)
from nautobot_dns_models.models import (
    DNSZoneModel,
    SRVRecordModel,
)
from nautobot_dns_models.tests import fixtures


class DnsZoneModelFilterTestCase(FilterTestCases.FilterTestCase):
    """DnsZoneModel Filter Test Case."""

    queryset = models.DnsZoneModel.objects.all()
    filterset = filters.DnsZoneModelFilterSet
    generic_filter_tests = (
        ("id",),
        ("created",),
        ("last_updated",),
        ("name",),
    )

    @classmethod
    def setUpTestData(cls):
        """Setup test data for DnsZoneModel Model."""
        fixtures.create_dnszonemodel()

    def test_q_search_name(self):
        """Test using Q search with name of DnsZoneModel."""
        params = {"q": "Test One"}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 1)

    def test_q_invalid(self):
        """Test using invalid Q search for DnsZoneModel."""
        params = {"q": "test-five"}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 0)


class SRVRecordModelFilterTestCase(TestCase):
    """SRVRecordModel Filter Test Case."""

    queryset = SRVRecordModel.objects.all()
    filterset = SRVRecordModelFilterSet

    @classmethod
    def setUpTestData(cls):
        """Setup test data for SRVRecordModel Model."""
        zone = DNSZoneModel.objects.create(name="example.com")
        SRVRecordModel.objects.create(
            name="_sip._tcp",
            priority=10,
            weight=5,
            port=5060,
            target="sip.example.com",
            zone=zone,
        )
        SRVRecordModel.objects.create(
            name="_sip._tcp",
            priority=20,
            weight=10,
            port=5060,
            target="sip2.example.com",
            zone=zone,
        )
        SRVRecordModel.objects.create(
            name="_xmpp._tcp",
            priority=30,
            weight=15,
            port=5222,
            target="xmpp.example.com",
            zone=zone,
        )

    def test_single_name(self):
        """Test filter with name of SRVRecordModel."""
        params = {"name": "_sip._tcp"}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 2)

    def test_name(self):
        """Test filter with name of SRVRecordModel."""
        params = {"name__in": "_sip._tcp,_xmpp._tcp"}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 3)

    def test_name_invalid(self):
        """Test using invalid search for SRVRecordModel."""
        params = {"name": "wrong-name"}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 0)

    def test_port(self):
        """Test filter with port of SRVRecordModel."""
        params = {"port": 5060}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 2)

    def test_port_invalid(self):
        """Test using invalid port for SRVRecordModel."""
        params = {"port": 99999}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 0)

    def test_target(self):
        """Test filter with target of SRVRecordModel."""
        params = {"target": "sip.example.com"}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 1)

    def test_target_multiple(self):
        """Test filter with multiple target values of SRVRecordModel."""
        params = {"target": ["sip.example.com", "xmpp.example.com"]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 2)

    def test_target_invalid(self):
        """Test using invalid target for SRVRecordModel."""
        params = {"target": "wrong-target"}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 0)

    def test_priority(self):
        """Test filter with priority of SRVRecordModel."""
        params = {"priority": 10}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 1)

    def test_weight(self):
        """Test filter with weight of SRVRecordModel."""
        params = {"weight": 5}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 1)

    def test_target_exact(self):
        """Test filter with exact target match of SRVRecordModel."""
        params = {"target": "sip.example.com"}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 1)
