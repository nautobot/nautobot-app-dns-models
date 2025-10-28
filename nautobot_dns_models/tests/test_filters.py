"""Test DNSZone Filter."""

from nautobot.apps.testing import FilterTestCases, TestCase
from nautobot.extras.models.statuses import Status
from nautobot.ipam.models import IPAddress, Namespace, Prefix
from nautobot.tenancy.models import Tenant, TenantGroup

from nautobot_dns_models.filters import (
    AAAARecordFilterSet,
    ARecordFilterSet,
    CNAMERecordFilterSet,
    DNSViewFilterSet,
    DNSViewPrefixAssignmentFilterSet,
    DNSZoneFilterSet,
    MXRecordFilterSet,
    NSRecordFilterSet,
    PTRRecordFilterSet,
    SRVRecordFilterSet,
    TXTRecordFilterSet,
)
from nautobot_dns_models.models import (
    AAAARecord,
    ARecord,
    CNAMERecord,
    DNSView,
    DNSViewPrefixAssignment,
    DNSZone,
    MXRecord,
    NSRecord,
    PTRRecord,
    SRVRecord,
    TXTRecord,
)


class DNSViewFilterTestCase(FilterTestCases.FilterTestCase):
    """DNSView Filter Test Case."""

    queryset = DNSView.objects.all()
    filterset = DNSViewFilterSet

    generic_filter_tests = [
        ["name"],
        ["description"],
        ["prefixes"],
    ]

    @classmethod
    def setUpTestData(cls):
        """Setup test data for DNSView Model."""
        namespace = Namespace.objects.get(name="Global")
        active_status = Status.objects.get(name="Active")
        cls.prefixes = (
            Prefix.objects.create(prefix="192.0.2.0/24", namespace=namespace, status=active_status),
            Prefix.objects.create(prefix="192.0.3.0/24", namespace=namespace, status=active_status),
            Prefix.objects.create(prefix="192.0.4.0/24", namespace=namespace, status=active_status),
            Prefix.objects.create(prefix="192.0.5.0/24", namespace=namespace, status=active_status),
            Prefix.objects.create(prefix="192.0.6.0/24", namespace=namespace, status=active_status),
        )

        dns_views = (
            DNSView.objects.create(name="Test One", description="Dns View 1"),
            DNSView.objects.create(name="Test Two", description="Dns View 2"),
            DNSView.objects.create(name="Test Three", description="Dns View 3"),
        )
        dns_views[0].prefixes.set([cls.prefixes[0]])
        dns_views[1].prefixes.set(cls.prefixes[2:4])

    def test_name(self):
        """Test using name search with name of DNSView."""
        params = {"name__ic": ["TEST T"]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 2)

    def test_name_invalid(self):
        """Test using invalid name search for DNSView."""
        params = {"name": "wrong-name"}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 0)

    def test_search(self):
        """Test filtering by Q search value."""
        self.assertEqual(self.filterset({"q": "Test One"}, self.queryset).qs.count(), 1)
        self.assertEqual(self.filterset({"q": "Test"}, self.queryset).qs.count(), 3)
        self.assertEqual(self.filterset({"q": "Two"}, self.queryset).qs.count(), 1)
        self.assertEqual(self.filterset({"q": "view"}, self.queryset).qs.count(), 0)


class DNSViewPrefixAssignmentFilterTestCase(FilterTestCases.FilterTestCase):
    """DNSViewPrefixAssignment Filter Test Case."""

    queryset = DNSViewPrefixAssignment.objects.all()
    filterset = DNSViewPrefixAssignmentFilterSet
    generic_filter_tests = [
        ["dns_view"],
        ["prefix"],
    ]

    @classmethod
    def setUpTestData(cls):
        """Setup test data for DNSViewPrefixAssignment Model."""
        namespace = Namespace.objects.get(name="Global")
        active_status = Status.objects.get(name="Active")
        cls.prefixes = (
            Prefix.objects.create(prefix="192.0.2.0/24", namespace=namespace, status=active_status),
            Prefix.objects.create(prefix="192.0.3.0/24", namespace=namespace, status=active_status),
            Prefix.objects.create(prefix="192.0.4.0/24", namespace=namespace, status=active_status),
        )

        cls.dns_views = (
            DNSView.objects.create(name="View 1", description="First DNS View"),
            DNSView.objects.create(name="View 2", description="Second DNS View"),
            DNSView.objects.create(name="View 3", description="Third DNS View"),
        )

        DNSViewPrefixAssignment.objects.create(dns_view=cls.dns_views[0], prefix=cls.prefixes[0])
        DNSViewPrefixAssignment.objects.create(dns_view=cls.dns_views[1], prefix=cls.prefixes[1])
        DNSViewPrefixAssignment.objects.create(dns_view=cls.dns_views[2], prefix=cls.prefixes[2])

    def test_search(self):
        """Test filtering by Q search value."""
        self.assertQuerysetEqualAndNotEmpty(
            self.filterset({"q": "View 1"}, self.queryset).qs,
            DNSViewPrefixAssignment.objects.filter(dns_view__name__icontains="View 1"),
            ordered=False,
        )
        self.assertQuerysetEqualAndNotEmpty(
            self.filterset({"q": "View"}, self.queryset).qs,
            DNSViewPrefixAssignment.objects.filter(dns_view__name__icontains="View"),
            ordered=False,
        )
        self.assertEqual(self.filterset({"q": "Nikos"}, self.queryset).qs.count(), 0)


class DNSZoneFilterTestCase(FilterTestCases.FilterTestCase, FilterTestCases.TenancyFilterTestCaseMixin):
    """DNSZone Filter Test Case."""

    queryset = DNSZone.objects.all()
    filterset = DNSZoneFilterSet
    tenancy_related_name = "dns_zones"

    generic_filter_tests = (
        ("id",),
        ("created",),
        ("last_updated",),
        ("name",),
        ("ttl",),
        ("filename",),
        ("description",),
        ("soa_expire",),
        ("soa_mname",),
        ("soa_rname",),
        ("soa_refresh",),
        ("soa_retry",),
        ("soa_serial",),
        ("soa_minimum",),
    )

    @classmethod
    def setUpTestData(cls):
        """Setup test data for DNSZone Model."""
        super().setUpTestData()

        cls.tenant_group1 = TenantGroup.objects.create(name="Test Tenant Group 1")
        cls.tenant_group2 = TenantGroup.objects.create(name="Test Tenant Group 2")
        cls.tenant1 = Tenant.objects.create(name="Test DNS Zone Tenant 1", tenant_group=cls.tenant_group1)
        cls.tenant2 = Tenant.objects.create(name="Test DNS Zone Tenant 2", tenant_group=cls.tenant_group2)

        DNSZone.objects.create(
            name="Test One",
            filename="zone1.conf",
            tenant=cls.tenant1,
            ttl=6400,
            description="Test zone one",
            soa_mname="ns1.example.com",
            soa_rname="admin.example.com",
            soa_refresh=7200,
            soa_expire=1209600,
            soa_minimum=9600,
        )
        DNSZone.objects.create(
            name="Test Two",
            filename="zone2.conf",
            tenant=cls.tenant2,
            soa_mname="ns2.example.com",
            description="Test zone two",
            ttl=7200,
            soa_serial=15,
            soa_refresh=74000,
            soa_retry=8900,
        )
        DNSZone.objects.create(
            name="Test Three",
            filename="zone3.conf",
            tenant=cls.tenant1,
            description="Test zone three",
            soa_rname="admin.admin.com",
            soa_serial=2024020101,
            soa_retry=9600,
            soa_expire=1209200,
            soa_minimum=7200,
        )

    def test_single_name(self):
        """Test using Q search with name of DNSZone."""
        params = {"name": "Test One"}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 1)

    def test_name(self):
        """Test using Q search with name of DNSZone."""
        params = {"name__in": "Test"}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 3)

    def test_name_invalid(self):
        """Test using invalid Q search for DNSZone."""
        params = {"name": "wrong-name"}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 0)

    def test_search(self):
        """Test filtering by Q search value."""
        self.assertEqual(self.filterset({"q": "Test One"}, self.queryset).qs.count(), 1)
        self.assertEqual(self.filterset({"q": "Test"}, self.queryset).qs.count(), 3)
        self.assertEqual(self.filterset({"q": "zone1"}, self.queryset).qs.count(), 1)
        self.assertEqual(self.filterset({"q": "zone"}, self.queryset).qs.count(), 3)


class NSRecordFilterTestCase(TestCase):
    """NSRecord Filter Test Case."""

    queryset = NSRecord.objects.all()
    filterset = NSRecordFilterSet

    @classmethod
    def setUpTestData(cls):
        """Setup test data for NSRecord Model."""
        zone = DNSZone.objects.create(name="example.com")
        NSRecord.objects.create(name="ns-01", server="ns1.example.com", zone=zone)
        NSRecord.objects.create(name="ns-02", server="ns2.example.com", zone=zone)
        NSRecord.objects.create(name="ns-02", server="ns3.example.com", zone=zone, ttl=7200)

    def test_single_name(self):
        """Test using Q search with name of NSRecord."""
        params = {"name": "ns-01"}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 1)

    def test_name(self):
        """Test using Q search with name of NSRecord."""
        params = {"name__ic": "ns"}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 3)

    def test_name_invalid(self):
        """Test using invalid Q search for NSRecord."""
        params = {"name": "wrong-name"}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 0)

    def test_server(self):
        """Test using Q search with server of NSRecord."""
        params = {"server": "ns1.example.com"}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 1)

    def test_server_in(self):
        """Test using Q search with server of NSRecord."""
        params = {"server__in": "example.com"}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 3)

    def test_server_invalid(self):
        """Test using invalid Q search for server of NSRecord."""
        params = {"server": "wrong-server"}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 0)

    def test_search(self):
        """Test filtering by Q search value."""
        self.assertEqual(self.filterset({"q": "ns-01"}, self.queryset).qs.count(), 1)
        self.assertEqual(self.filterset({"q": "ns-"}, self.queryset).qs.count(), 3)
        self.assertEqual(self.filterset({"q": "ns1"}, self.queryset).qs.count(), 1)
        self.assertEqual(self.filterset({"q": "example.com"}, self.queryset).qs.count(), 3)

    # Testing TTL filterset here. If it works in NSRecord, it should work in all other record types.
    def test_ttl_equals(self):
        """Test filter with TTL equal to value."""
        params = {"ttl": 7200}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 1)

    def test_ttl_greater(self):
        """Test filter with TTL greater than value."""
        params = {"ttl__gt": 7000}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 1)

    def test_ttl_greater_or_equal(self):
        """Test filter with TTL greater than or equal to value."""
        params = {"ttl__gte": 3600}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 3)

    def test_ttl_less(self):
        """Test filter with TTL less than value."""
        params = {"ttl__lt": 4000}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 2)

    def test_ttl_less_or_equal(self):
        """Test filter with TTL less than or equal to value."""
        params = {"ttl__lte": 3600}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 2)

    def test_ttl_not_equal(self):
        """Test filter with TTL not equal to value."""
        params = {"ttl__ne": 3600}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 1)


class ARecordFilterTestCase(TestCase):
    """ARecord Filter Test Case."""

    queryset = ARecord.objects.all()
    filterset = ARecordFilterSet

    @classmethod
    def setUpTestData(cls):
        """Setup test data for ARecord Model."""
        cls.zone = DNSZone.objects.create(name="example.com")
        status = Status.objects.get(name="Active")
        namespace = Namespace.objects.get(name="Global")
        Prefix.objects.create(prefix="10.0.0.0/24", namespace=namespace, type="Pool", status=status)
        cls.ip_addresses = (
            IPAddress.objects.create(address="10.0.0.1/32", namespace=namespace, status=status),
            IPAddress.objects.create(address="10.0.0.2/32", namespace=namespace, status=status),
            IPAddress.objects.create(address="10.0.0.3/32", namespace=namespace, status=status),
        )

        ARecord.objects.create(name="a-record-01", ip_address=cls.ip_addresses[0], zone=cls.zone)
        ARecord.objects.create(name="a-record-02", ip_address=cls.ip_addresses[1], zone=cls.zone)
        ARecord.objects.create(name="a-record-03", ip_address=cls.ip_addresses[2], zone=cls.zone)

    def test_single_name(self):
        """Test filter with name of ARecord."""
        params = {"name": "a-record-01"}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 1)

    def test_name(self):
        """Test filter with name of ARecord."""
        params = {"name__ic": "a-record"}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 3)

    def test_name_invalid(self):
        """Test using invalid search for ARecord."""
        params = {"name": "wrong-name"}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 0)

    def test_ipaddress(self):
        """Test search with IP address of ARecord."""
        params = {"ip_address": [self.ip_addresses[0]]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 1)

    def test_ipaddress_in(self):
        """Test ip_address in ARecord."""
        params = {"ip_address__in": "10.0.0."}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 3)

    def test_zone(self):
        params = {"zone": self.zone}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 3)

    def test_search(self):
        """Test filtering by Q search value."""
        self.assertEqual(self.filterset({"q": "a-record-01"}, self.queryset).qs.count(), 1)
        self.assertEqual(self.filterset({"q": "a-record"}, self.queryset).qs.count(), 3)
        self.assertEqual(self.filterset({"q": self.ip_addresses[0].host}, self.queryset).qs.count(), 1)
        self.assertEqual(self.filterset({"q": "example.com"}, self.queryset).qs.count(), 3)


class AAAARecordFilterTestCase(TestCase):
    """AAAARecord Filter Test Case."""

    queryset = AAAARecord.objects.all()
    filterset = AAAARecordFilterSet

    @classmethod
    def setUpTestData(cls):
        """Setup test data for ARecord Model."""
        zone = DNSZone.objects.create(name="example.com")
        status = Status.objects.get(name="Active")
        namespace = Namespace.objects.get(name="Global")
        Prefix.objects.create(prefix="2001:db8:abcd:12::/64", namespace=namespace, type="Pool", status=status)
        cls.ip_addresses = (
            IPAddress.objects.create(address="2001:db8:abcd:12::1/128", namespace=namespace, status=status),
            IPAddress.objects.create(address="2001:db8:abcd:12::2/128", namespace=namespace, status=status),
            IPAddress.objects.create(address="2001:db8:abcd:12::3/128", namespace=namespace, status=status),
        )

        AAAARecord.objects.create(name="aaaa-record-01", ip_address=cls.ip_addresses[0], zone=zone)
        AAAARecord.objects.create(name="aaaa-record-02", ip_address=cls.ip_addresses[1], zone=zone)
        AAAARecord.objects.create(name="aaaa-record-03", ip_address=cls.ip_addresses[2], zone=zone)

    def test_single_name(self):
        """Test filter with name of AAAARecord."""
        params = {"name": "aaaa-record-01"}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 1)

    def test_name(self):
        """Test filter with name of AAAARecord."""
        params = {"name__in": "aaaa-record"}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 3)

    def test_name_invalid(self):
        """Test using invalid search for AAAARecord."""
        params = {"name": "wrong-name"}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 0)

    def test_ip_address(self):
        """Test search with IP address of AAAARecord."""
        params = {"ip_address": [self.ip_addresses[0]]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 1)

    def test_ip_address_in(self):
        """Test ip_address in AAAARecord."""
        params = {"ip_address__in": "2001:db8:abcd:12::"}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 3)

    def test_search(self):
        """Test filtering by Q search value."""
        self.assertEqual(self.filterset({"q": "aaaa-record-01"}, self.queryset).qs.count(), 1)
        self.assertEqual(self.filterset({"q": "aaaa-record"}, self.queryset).qs.count(), 3)
        self.assertEqual(self.filterset({"q": self.ip_addresses[0].host}, self.queryset).qs.count(), 1)
        self.assertEqual(self.filterset({"q": "example.com"}, self.queryset).qs.count(), 3)


class CNAMERecordFilterTestCase(TestCase):
    """CNAMERecord Filter Test Case."""

    queryset = CNAMERecord.objects.all()
    filterset = CNAMERecordFilterSet

    @classmethod
    def setUpTestData(cls):
        zone = DNSZone.objects.create(name="example.com")
        CNAMERecord.objects.create(name="cname-record-01", alias="site.example.com", zone=zone)
        CNAMERecord.objects.create(name="cname-record-02", alias="blog.example.com", zone=zone)

    def test_single_name(self):
        """Test filter with name of CNAMERecord."""
        params = {"name": "cname-record-01"}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 1)

    def test_name(self):
        """Test filter with name of CNAMERecord."""
        params = {"name__in": "cname-record"}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 2)

    def test_name_invalid(self):
        """Test using invalid search for CNAMERecord."""
        params = {"name": "wrong-name"}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 0)

    def test_alias(self):
        """Test search with alias of CNAMERecord."""
        params = {"alias": "site.example.com"}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 1)

    def test_alias_in(self):
        """Test alias in CNAMERecord."""
        params = {"alias__in": "example.com"}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 2)

    def test_alias_invalid(self):
        params = {"alias": "wrong-alias"}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 0)

    def test_search(self):
        """Test filtering by Q search value."""
        self.assertEqual(self.filterset({"q": "cname-record-01"}, self.queryset).qs.count(), 1)
        self.assertEqual(self.filterset({"q": "cname-record"}, self.queryset).qs.count(), 2)
        self.assertEqual(self.filterset({"q": "site"}, self.queryset).qs.count(), 1)
        self.assertEqual(self.filterset({"q": "example.com"}, self.queryset).qs.count(), 2)


class MXRecordFilterTestCase(TestCase):
    """MXRecord Filter Test Case."""

    queryset = MXRecord.objects.all()
    filterset = MXRecordFilterSet

    @classmethod
    def setUpTestData(cls):
        zone = DNSZone.objects.create(name="example.com")
        MXRecord.objects.create(name="mx-record-01", mail_server="mail.example.com", zone=zone)
        MXRecord.objects.create(name="mx-record-02", mail_server="mail-02.example.com", zone=zone)

    def test_single_name(self):
        """Test filter with name of MXRecord."""
        params = {"name": "mx-record-01"}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 1)

    def test_name(self):
        """Test filter with name of MXRecord."""
        params = {"name__in": "mx-record"}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 2)

    def test_name_invalid(self):
        """Test using invalid search for MXRecord."""
        params = {"name": "wrong-name"}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 0)

    def test_mail_server(self):
        """Test search with mail server of MXRecord."""
        params = {"mail_server": "mail.example.com"}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 1)

    def test_mail_server_in(self):
        """Test mail server in MXRecord."""
        params = {"mail_server__in": "example.com"}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 2)

    def test_mail_server_invalid(self):
        params = {"mail_server": "wrong-mail-server"}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 0)

    def test_search(self):
        """Test filtering by Q search value."""
        self.assertEqual(self.filterset({"q": "mx-record-01"}, self.queryset).qs.count(), 1)
        self.assertEqual(self.filterset({"q": "mx-record"}, self.queryset).qs.count(), 2)
        self.assertEqual(self.filterset({"q": "mail-02"}, self.queryset).qs.count(), 1)
        self.assertEqual(self.filterset({"q": "example.com"}, self.queryset).qs.count(), 2)


class TXTRecordFilterTestCase(TestCase):
    """TXTRecord Filter Test Case."""

    queryset = TXTRecord.objects.all()
    filterset = TXTRecordFilterSet

    @classmethod
    def setUpTestData(cls):
        zone = DNSZone.objects.create(name="example.com")
        TXTRecord.objects.create(name="txt-record-01", text="spf-record", zone=zone)
        TXTRecord.objects.create(name="txt-record-02", text="dkim-record", zone=zone)

    def test_single_name(self):
        """Test filter with name of TXTRecord."""
        params = {"name": "txt-record-01"}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 1)

    def test_name(self):
        """Test filter with name of TXTRecord."""
        params = {"name__in": "txt-record"}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 2)

    def test_name_invalid(self):
        """Test using invalid search for TXTRecord."""
        params = {"name": "wrong-name"}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 0)

    def test_text(self):
        """Test search with text of TXTRecord."""
        params = {"text": "spf-record"}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 1)

    def test_text_in(self):
        """Test text in TXTRecord."""
        params = {"text__in": "record"}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 2)

    def test_text_invalid(self):
        params = {"text": "wrong-text"}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 0)

    def test_search(self):
        """Test filtering by Q search value."""
        self.assertEqual(self.filterset({"q": "txt-record-01"}, self.queryset).qs.count(), 1)
        self.assertEqual(self.filterset({"q": "txt-record"}, self.queryset).qs.count(), 2)
        self.assertEqual(self.filterset({"q": "spf-record"}, self.queryset).qs.count(), 1)
        self.assertEqual(self.filterset({"q": "example.com"}, self.queryset).qs.count(), 2)


class PTRRecordFilterTestCase(TestCase):
    """PTRRecord Filter Test Case."""

    queryset = PTRRecord.objects.all()
    filterset = PTRRecordFilterSet

    @classmethod
    def setUpTestData(cls):
        zone = DNSZone.objects.create(name="example.com")
        PTRRecord.objects.create(name="ptr-record-01", ptrdname="ptr-record-01", zone=zone)
        PTRRecord.objects.create(name="ptr-record-02", ptrdname="ptr-record-02", zone=zone)

    def test_single_name(self):
        """Test filter with name of PTRRecord."""
        params = {"name": "ptr-record-01"}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 1)

    def test_name(self):
        """Test filter with name of PTRRecord."""
        params = {"name__in": "ptr-record"}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 2)

    def test_name_invalid(self):
        """Test using invalid search for PTRRecord."""
        params = {"name": "wrong-name"}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 0)

    def test_ptrdname(self):
        """Test search with ptrdname of PTRRecord."""
        params = {"ptrdname": "ptr-record-01"}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 1)

    def test_ptrdname_in(self):
        """Test ptrdname in PTRRecord."""
        params = {"ptrdname__in": "ptr-record"}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 2)

    def test_ptrdname_invalid(self):
        params = {"ptrdname": "wrong-ptrdname"}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 0)

    def test_search(self):
        """Test filtering by Q search value."""
        self.assertEqual(self.filterset({"q": "ptr-record-01"}, self.queryset).qs.count(), 1)
        self.assertEqual(self.filterset({"q": "ptr-record"}, self.queryset).qs.count(), 2)
        self.assertEqual(self.filterset({"q": "example.com"}, self.queryset).qs.count(), 2)


class SRVRecordFilterTestCase(TestCase):
    """SRVRecord Filter Test Case."""

    queryset = SRVRecord.objects.all()
    filterset = SRVRecordFilterSet

    @classmethod
    def setUpTestData(cls):
        """Setup test data for SRVRecord Model."""
        zone = DNSZone.objects.create(name="example.com")
        SRVRecord.objects.create(
            name="_sip._tcp",
            priority=10,
            weight=5,
            port=5060,
            target="sip.example.com",
            zone=zone,
        )
        SRVRecord.objects.create(
            name="_sip._tcp",
            priority=20,
            weight=10,
            port=5060,
            target="sip2.example.com",
            zone=zone,
        )
        SRVRecord.objects.create(
            name="_xmpp._tcp",
            priority=30,
            weight=15,
            port=5222,
            target="xmpp.example.com",
            zone=zone,
        )

    def test_single_name(self):
        """Test filter with name of SRVRecord."""
        params = {"name": "_sip._tcp"}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 2)

    def test_name(self):
        """Test filter with name of SRVRecord."""
        params = {"name__in": "_sip._tcp,_xmpp._tcp"}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 3)

    def test_name_invalid(self):
        """Test using invalid search for SRVRecord."""
        params = {"name": "wrong-name"}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 0)

    def test_port(self):
        """Test filter with port of SRVRecord."""
        params = {"port": 5060}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 2)

    def test_port_invalid(self):
        """Test using invalid port for SRVRecord."""
        params = {"port": 99999}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 0)

    def test_target(self):
        """Test filter with target of SRVRecord."""
        params = {"target": "sip.example.com"}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 1)

    def test_target_multiple(self):
        """Test filter with multiple target values of SRVRecord."""
        params = {"target": ["sip.example.com", "xmpp.example.com"]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 2)

    def test_target_invalid(self):
        """Test using invalid target for SRVRecord."""
        params = {"target": "wrong-target"}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 0)

    def test_priority(self):
        """Test filter with priority of SRVRecord."""
        params = {"priority": 10}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 1)

    def test_weight(self):
        """Test filter with weight of SRVRecord."""
        params = {"weight": 5}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 1)

    def test_target_exact(self):
        """Test filter with exact target match of SRVRecord."""
        params = {"target": "sip.example.com"}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 1)

    def test_search(self):
        """Test filtering by Q search value."""
        self.assertEqual(self.filterset({"q": "_sip._tcp"}, self.queryset).qs.count(), 2)
        self.assertEqual(self.filterset({"q": "sip2"}, self.queryset).qs.count(), 1)
        self.assertEqual(self.filterset({"q": "example.com"}, self.queryset).qs.count(), 3)
