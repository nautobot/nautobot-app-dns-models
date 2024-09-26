"""Test DnsZoneModel Filter."""

from django.test import TestCase
from nautobot.extras.models.statuses import Status
from nautobot.ipam.models import IPAddress, Namespace, Prefix

from nautobot_dns_models.filters import (
    AAAARecordModelFilterSet,
    ARecordModelFilterSet,
    CNAMERecordModelFilterSet,
    DNSZoneModelFilterSet,
    MXRecordModelFilterSet,
    NSRecordModelFilterSet,
    PTRRecordModelFilterSet,
    TXTRecordModelFilterSet,
)
from nautobot_dns_models.models import (
    AAAARecordModel,
    ARecordModel,
    CNAMERecordModel,
    DNSZoneModel,
    MXRecordModel,
    NSRecordModel,
    PTRRecordModel,
    TXTRecordModel,
)
from nautobot_dns_models.tests import fixtures


class DNSZoneModelFilterTestCase(TestCase):
    """DnsZoneModel Filter Test Case."""

    queryset = DNSZoneModel.objects.all()
    filterset = DNSZoneModelFilterSet

    @classmethod
    def setUpTestData(cls):
        """Setup test data for DnsZoneModel Model."""
        DNSZoneModel.objects.create(name="Test One")
        DNSZoneModel.objects.create(name="Test Two")
        DNSZoneModel.objects.create(name="Test Three")

    def test_single_name(self):
        """Test using Q search with name of DnsZoneModel."""
        params = {"name": "Test One"}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 1)

    def test_name(self):
        """Test using Q search with name of DnsZoneModel."""
        params = {"name__in": "Test"}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 3)

    def test_name_invalid(self):
        """Test using invalid Q search for DnsZoneModel."""
        params = {"name": "wrong-name"}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 0)


class NSRecordModelFilterTestCase(TestCase):
    """NSRecordModel Filter Test Case."""

    queryset = NSRecordModel.objects.all()
    filterset = NSRecordModelFilterSet

    @classmethod
    def setUpTestData(cls):
        """Setup test data for NSRecordModel Model."""
        zone = DNSZoneModel.objects.create(name="example.com")
        NSRecordModel.objects.create(name="ns-01", server="ns1.example.com", zone=zone)
        NSRecordModel.objects.create(name="ns-02", server="ns2.example.com", zone=zone)
        NSRecordModel.objects.create(name="ns-02", server="ns3.example.com", zone=zone)

    def test_single_name(self):
        """Test using Q search with name of NSRecordModel."""
        params = {"name": "ns-01"}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 1)

    def test_name(self):
        """Test using Q search with name of NSRecordModel."""
        params = {"name__in": "ns"}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 3)

    def test_name_invalid(self):
        """Test using invalid Q search for NSRecordModel."""
        params = {"name": "wrong-name"}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 0)

    def test_server(self):
        """Test using Q search with server of NSRecordModel."""
        params = {"server": "ns1.example.com"}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 1)

    def test_server_in(self):
        """Test using Q search with server of NSRecordModel."""
        params = {"server__in": "example.com"}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 3)

    def test_server_invalid(self):
        params = {"server": "wrong-server"}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 0)

class ARecordModelFilterTestCase(TestCase):
    """ARecordModel Filter Test Case."""

    queryset = ARecordModel.objects.all()
    filterset = ARecordModelFilterSet

    @classmethod
    def setUpTestData(cls):
        """Setup test data for ARecordModel Model."""
        zone = DNSZoneModel.objects.create(name="example.com")
        status = Status.objects.get(name="Active")
        namespace = Namespace.objects.get(name="Global")
        Prefix.objects.create(prefix="10.0.0.0/24", namespace=namespace, type="Pool", status=status)
        cls.ip_addresses = (
        IPAddress.objects.create(address="10.0.0.1/32", namespace=namespace, status=status),
        IPAddress.objects.create(address="10.0.0.2/32", namespace=namespace, status=status),
        IPAddress.objects.create(address="10.0.0.3/32", namespace=namespace, status=status),
        )

        ARecordModel.objects.create(name="a-record-01", address=cls.ip_addresses[0], zone=zone)
        ARecordModel.objects.create(name="a-record-02", address=cls.ip_addresses[1], zone=zone)
        ARecordModel.objects.create(name="a-record-03", address=cls.ip_addresses[2], zone=zone)

    def test_single_name(self):
        """Test filter with name of ARecordModel."""
        params = {"name": "a-record-01"}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 1)

    def test_name(self):
        """Test filter with name of ARecordModel."""
        params = {"name__in": "a-record"}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 3)

    def test_name_invalid(self):
        """Test using invalid search for ARecordModel."""
        params = {"name": "wrong-name"}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 0)

    def test_address(self):
        """Test search with IP address of ARecordModel."""
        params = {"address": self.ip_addresses[0]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 1)

    def test_address_in(self):
        """Test address in ARecordModel."""
        params = {"address__in": "10.0.0."}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 3)

    # FIXME: fix below test cases for Arecord
    # def test_address_invalid(self):
    #     params = {"address": "10.0.0.5/32"}
    #     self.assertEqual(self.filterset(params, self.queryset).qs.count(), 0)

    # def test_zone_invalid(self):
    #     params = {"zone": "wrong-zone"}
    #     self.assertEqual(self.filterset(params, self.queryset).qs.count(), 0)

# TODO: add more filters test cases