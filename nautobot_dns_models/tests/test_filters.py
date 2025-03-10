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
        cls.zone = DNSZoneModel.objects.create(name="example.com")
        status = Status.objects.get(name="Active")
        namespace = Namespace.objects.get(name="Global")
        Prefix.objects.create(prefix="10.0.0.0/24", namespace=namespace, type="Pool", status=status)
        cls.ip_addresses = (
            IPAddress.objects.create(address="10.0.0.1/32", namespace=namespace, status=status),
            IPAddress.objects.create(address="10.0.0.2/32", namespace=namespace, status=status),
            IPAddress.objects.create(address="10.0.0.3/32", namespace=namespace, status=status),
        )

        ARecordModel.objects.create(name="a-record-01", address=cls.ip_addresses[0], zone=cls.zone)
        ARecordModel.objects.create(name="a-record-02", address=cls.ip_addresses[1], zone=cls.zone)
        ARecordModel.objects.create(name="a-record-03", address=cls.ip_addresses[2], zone=cls.zone)

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

    def test_zone(self):
        params = {"zone": self.zone}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 3)


class AAAARecordModelFilterTestCase(TestCase):
    """AAAARecordModel Filter Test Case."""

    queryset = AAAARecordModel.objects.all()
    filterset = AAAARecordModelFilterSet

    @classmethod
    def setUpTestData(cls):
        """Setup test data for ARecordModel Model."""
        zone = DNSZoneModel.objects.create(name="example.com")
        status = Status.objects.get(name="Active")
        namespace = Namespace.objects.get(name="Global")
        Prefix.objects.create(prefix="2001:db8:abcd:12::/64", namespace=namespace, type="Pool", status=status)
        cls.ip_addresses = (
            IPAddress.objects.create(address="2001:db8:abcd:12::1/128", namespace=namespace, status=status),
            IPAddress.objects.create(address="2001:db8:abcd:12::2/128", namespace=namespace, status=status),
            IPAddress.objects.create(address="2001:db8:abcd:12::3/128", namespace=namespace, status=status),
        )

        AAAARecordModel.objects.create(name="aaaa-record-01", address=cls.ip_addresses[0], zone=zone)
        AAAARecordModel.objects.create(name="aaaa-record-02", address=cls.ip_addresses[1], zone=zone)
        AAAARecordModel.objects.create(name="aaaa-record-03", address=cls.ip_addresses[2], zone=zone)

    def test_single_name(self):
        """Test filter with name of AAAARecordModel."""
        params = {"name": "aaaa-record-01"}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 1)

    def test_name(self):
        """Test filter with name of AAAARecordModel."""
        params = {"name__in": "aaaa-record"}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 3)

    def test_name_invalid(self):
        """Test using invalid search for AAAARecordModel."""
        params = {"name": "wrong-name"}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 0)

    def test_address(self):
        """Test search with IP address of AAAARecordModel."""
        params = {"address": self.ip_addresses[0]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 1)

    def test_address_in(self):
        """Test address in AAAARecordModel."""
        params = {"address__in": "2001:db8:abcd:12::"}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 3)


class CNAMERecordModelFilterTestCase(TestCase):
    """CNAMERecordModel Filter Test Case."""

    queryset = CNAMERecordModel.objects.all()
    filterset = CNAMERecordModelFilterSet

    @classmethod
    def setUpTestData(cls):
        zone = DNSZoneModel.objects.create(name="example.com")
        CNAMERecordModel.objects.create(name="cname-record-01", alias="site.example.com", zone=zone)
        CNAMERecordModel.objects.create(name="cname-record-02", alias="blog.example.com", zone=zone)

    def test_single_name(self):
        """Test filter with name of CNAMERecordModel."""
        params = {"name": "cname-record-01"}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 1)

    def test_name(self):
        """Test filter with name of CNAMERecordModel."""
        params = {"name__in": "cname-record"}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 2)

    def test_name_invalid(self):
        """Test using invalid search for CNAMERecordModel."""
        params = {"name": "wrong-name"}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 0)

    def test_alias(self):
        """Test search with alias of CNAMERecordModel."""
        params = {"alias": "site.example.com"}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 1)

    def test_alias_in(self):
        """Test alias in CNAMERecordModel."""
        params = {"alias__in": "example.com"}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 2)

    def test_alias_invalid(self):
        params = {"alias": "wrong-alias"}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 0)


class MXRecordModelFilterTestCase(TestCase):
    """MXRecordModel Filter Test Case."""

    queryset = MXRecordModel.objects.all()
    filterset = MXRecordModelFilterSet

    @classmethod
    def setUpTestData(cls):
        zone = DNSZoneModel.objects.create(name="example.com")
        MXRecordModel.objects.create(name="mx-record-01", mail_server="mail.example.com", zone=zone)
        MXRecordModel.objects.create(name="mx-record-02", mail_server="mail-02.example.com", zone=zone)

    def test_single_name(self):
        """Test filter with name of MXRecordModel."""
        params = {"name": "mx-record-01"}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 1)

    def test_name(self):
        """Test filter with name of MXRecordModel."""
        params = {"name__in": "mx-record"}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 2)

    def test_name_invalid(self):
        """Test using invalid search for MXRecordModel."""
        params = {"name": "wrong-name"}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 0)

    def test_mail_server(self):
        """Test search with mail server of MXRecordModel."""
        params = {"mail_server": "mail.example.com"}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 1)

    def test_mail_server_in(self):
        """Test mail server in MXRecordModel."""
        params = {"mail_server__in": "example.com"}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 2)

    def test_mail_server_invalid(self):
        params = {"mail_server": "wrong-mail-server"}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 0)


class TXTRecordModelFilterTestCase(TestCase):
    """TXTRecordModel Filter Test Case."""

    queryset = TXTRecordModel.objects.all()
    filterset = TXTRecordModelFilterSet

    @classmethod
    def setUpTestData(cls):
        zone = DNSZoneModel.objects.create(name="example.com")
        TXTRecordModel.objects.create(name="txt-record-01", text="spf-record", zone=zone)
        TXTRecordModel.objects.create(name="txt-record-02", text="dkim-record", zone=zone)

    def test_single_name(self):
        """Test filter with name of TXTRecordModel."""
        params = {"name": "txt-record-01"}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 1)

    def test_name(self):
        """Test filter with name of TXTRecordModel."""
        params = {"name__in": "txt-record"}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 2)

    def test_name_invalid(self):
        """Test using invalid search for TXTRecordModel."""
        params = {"name": "wrong-name"}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 0)

    def test_text(self):
        """Test search with text of TXTRecordModel."""
        params = {"text": "spf-record"}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 1)

    def test_text_in(self):
        """Test text in TXTRecordModel."""
        params = {"text__in": "record"}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 2)

    def test_text_invalid(self):
        params = {"text": "wrong-text"}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 0)


class PTRRecordModelFilterTestCase(TestCase):
    """PTRRecordModel Filter Test Case."""

    queryset = PTRRecordModel.objects.all()
    filterset = PTRRecordModelFilterSet

    @classmethod
    def setUpTestData(cls):
        zone = DNSZoneModel.objects.create(name="example.com")
        PTRRecordModel.objects.create(name="ptr-record-01", ptrdname="ptr-record-01", zone=zone)
        PTRRecordModel.objects.create(name="ptr-record-02", ptrdname="ptr-record-02", zone=zone)

    def test_single_name(self):
        """Test filter with name of PTRRecordModel."""
        params = {"name": "ptr-record-01"}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 1)

    def test_name(self):
        """Test filter with name of PTRRecordModel."""
        params = {"name__in": "ptr-record"}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 2)

    def test_name_invalid(self):
        """Test using invalid search for PTRRecordModel."""
        params = {"name": "wrong-name"}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 0)

    def test_ptrdname(self):
        """Test search with ptrdname of PTRRecordModel."""
        params = {"ptrdname": "ptr-record-01"}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 1)

    def test_ptrdname_in(self):
        """Test ptrdname in PTRRecordModel."""
        params = {"ptrdname__in": "ptr-record"}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 2)

    def test_ptrdname_invalid(self):
        params = {"ptrdname": "wrong-ptrdname"}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 0)
