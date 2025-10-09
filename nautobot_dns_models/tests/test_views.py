"""Unit tests for views."""

from constance import config as constance_config
from django.contrib.auth import get_user_model
from django.test import override_settings
from django.urls import reverse
from nautobot.apps.testing import ViewTestCases
from nautobot.core.testing.utils import extract_page_body
from nautobot.extras.models import Status
from nautobot.ipam.choices import PrefixTypeChoices
from nautobot.ipam.models import IPAddress, Namespace, Prefix
from netutils.ip import ipaddress_address

from nautobot_dns_models.models import (
    AAAARecord,
    ARecord,
    CNAMERecord,
    DNSZone,
    MXRecord,
    NSRecord,
    PTRRecord,
    SRVRecord,
    TXTRecord,
)

User = get_user_model()


class DnsZoneViewTest(ViewTestCases.PrimaryObjectViewTestCase):
    # pylint: disable=too-many-ancestors
    """Test the DNSZone views."""

    model = DNSZone

    @classmethod
    def setUpTestData(cls):
        DNSZone.objects.create(
            name="example-one.com",
            filename="test one",
            soa_mname="auth-server",
            soa_rname="admin@example-one.com",
            soa_refresh=86400,
            soa_retry=7200,
            soa_expire=3600000,
            soa_serial=0,
            soa_minimum=172800,
        )
        DNSZone.objects.create(
            name="example-two.com",
            filename="test two",
            soa_mname="auth-server",
            soa_rname="admin@example-two.com",
            soa_refresh=86400,
            soa_retry=7200,
            soa_expire=3600000,
            soa_serial=0,
            soa_minimum=172800,
        )
        DNSZone.objects.create(
            name="example-three.com",
            filename="test three",
            soa_mname="auth-server",
            soa_rname="admin@example-three.com",
            soa_refresh=86400,
            soa_retry=7200,
            soa_expire=3600000,
            soa_serial=0,
            soa_minimum=172800,
        )

        cls.form_data = {
            "name": "Test 1",
            "ttl": 3600,
            "description": "Initial model",
            "filename": "test three",
            "soa_mname": "auth-server",
            "soa_rname": "admin@example-three.com",
            "soa_refresh": 86400,
            "soa_retry": 7200,
            "soa_expire": 3600000,
            "soa_serial": 0,
            "soa_minimum": 172800,
        }

        cls.csv_data = (
            "name, ttl, description, filename, soa_mname, soa_rname, soa_refresh, soa_retry, soa_expire, soa_serial, soa_minimum",
            "Test 3, 3600, Description 3, filename 3, auth-server, admin@example_three.com, 86400, 7200, 3600000, 0, 172800",
        )

        cls.bulk_edit_data = {"description": "Bulk edit views"}


class NSRecordViewTest(ViewTestCases.PrimaryObjectViewTestCase):
    # pylint: disable=too-many-ancestors
    """Test the NSRecord views."""

    model = NSRecord

    @classmethod
    def setUpTestData(cls):
        zone = DNSZone.objects.create(
            name="example_one.com",
        )

        NSRecord.objects.create(
            name="primary",
            server="example-server.com.",
            zone=zone,
        )
        NSRecord.objects.create(
            name="secondary",
            server="example-server.com.",
            zone=zone,
        )
        NSRecord.objects.create(
            name="tertiary",
            server="example-server.com.",
            zone=zone,
        )

        cls.form_data = {
            "name": "test record",
            "server": "test server",
            "zone": zone.pk,
            "ttl": 3600,
        }

        cls.csv_data = (
            "name,server,zone, ttl",
            f"Test 3,server 3,{zone.name}, 3600",
        )

        cls.bulk_edit_data = {"description": "Bulk edit views"}


class ARecordViewTest(ViewTestCases.PrimaryObjectViewTestCase):
    # pylint: disable=too-many-ancestors, too-many-locals
    """Test the ARecord views."""

    model = ARecord

    @classmethod
    def setUpTestData(cls):
        zone = DNSZone.objects.create(
            name="example_one.com",
        )
        status = Status.objects.get(name="Active")
        namespace = Namespace.objects.get(name="Global")
        Prefix.objects.create(prefix="10.0.0.0/24", namespace=namespace, type="Pool", status=status)
        ip_addresses = (
            IPAddress.objects.create(address="10.0.0.1/32", namespace=namespace, status=status),
            IPAddress.objects.create(address="10.0.0.2/32", namespace=namespace, status=status),
            IPAddress.objects.create(address="10.0.0.3/32", namespace=namespace, status=status),
        )

        ARecord.objects.create(
            name="primary",
            address=ip_addresses[0],
            zone=zone,
        )
        ARecord.objects.create(
            name="primary",
            address=ip_addresses[1],
            zone=zone,
        )
        ARecord.objects.create(
            name="primary",
            address=ip_addresses[2],
            zone=zone,
        )

        cls.form_data = {
            "name": "test record",
            "address": ip_addresses[0].pk,
            "ttl": 3600,
            "zone": zone.pk,
        }

        cls.csv_data = (
            "name,address,zone",
            f"Test 3,{ip_addresses[0].pk},{zone.name}",
        )

        cls.bulk_edit_data = {"description": "Bulk edit views"}

    def helper_for_ipaddress_detail_view_side_panel(self, show_panel: str, when_not_present: bool, when_present: bool):
        """Test IP Address side panel for A Records."""
        namespace = Namespace.objects.get(name="Global")
        status = Status.objects.get(name="Active")
        address = IPAddress.objects.create(address="10.0.0.251/29", status=status, namespace=namespace)
        other_address = IPAddress.objects.create(address="10.0.0.252/29", status=status, namespace=namespace)
        zone = DNSZone.objects.get(name="example_one.com")
        constance_config.nautobot_dns_models__SHOW_FORWARD_PANEL = show_panel

        # Base HTTP test to IP detail view
        url = reverse("ipam:ipaddress", args=(address.pk,))
        response = self.client.get(url)
        self.assertHttpStatus(response, 200)
        content = extract_page_body(response.content.decode(response.charset))

        # Assert A Record pane when A Record is not present
        self.assertInHTML("<strong>A Records</strong>", content, int(when_not_present))
        component = "— No A Records found —"
        self.assertInHTML(component, content, int(when_not_present))

        # Create A Record and refresh page content
        a_record = ARecord.objects.create(name="one", zone=zone, address=address)
        response = self.client.get(url)
        self.assertHttpStatus(response, 200)
        content = extract_page_body(response.content.decode(response.charset))

        # Assert A Record pane when A Record is present
        self.assertInHTML("<strong>A Records</strong>", content, int(when_present))
        arecord_url = reverse("plugins:nautobot_dns_models:arecord", args=(a_record.pk,))
        component = f'<a href="{arecord_url}">{a_record.name}</a>'
        self.assertInHTML(component, content, int(when_present))

        # Create irrelevant A Record and verify it is not shown
        other_a_record = ARecord.objects.create(name="other", zone=zone, address=other_address)
        other_arecord_url = reverse("plugins:nautobot_dns_models:arecord", args=(other_a_record.pk,))
        other_component = f'<a href="{other_arecord_url}">{other_a_record.name}</a>'
        self.assertInHTML(other_component, content, 0)

    @override_settings(EXEMPT_VIEW_PERMISSIONS=["*"])
    def test_ipaddress_detail_view_side_panel_always(self):
        """Test IP Address side panel for A Records when set to 'Always'."""
        self.helper_for_ipaddress_detail_view_side_panel(show_panel="always", when_not_present=True, when_present=True)

    @override_settings(EXEMPT_VIEW_PERMISSIONS=["*"])
    def test_ipaddress_detail_view_side_panel_present(self):
        """Test IP Address side panel for A Records when set to 'If present'."""
        self.helper_for_ipaddress_detail_view_side_panel(
            show_panel="if_present", when_not_present=False, when_present=True
        )

    @override_settings(EXEMPT_VIEW_PERMISSIONS=["*"])
    def test_ipaddress_detail_view_side_panel_never(self):
        """Test IP Address side panel for A Records when set to 'Never'."""
        self.helper_for_ipaddress_detail_view_side_panel(show_panel="never", when_not_present=False, when_present=False)


class AAAARecordViewTest(ViewTestCases.PrimaryObjectViewTestCase):
    # pylint: disable=too-many-ancestors, too-many-locals
    """Test the AAAARecord views."""

    model = AAAARecord

    @classmethod
    def setUpTestData(cls):
        zone = DNSZone.objects.create(
            name="example_one.com",
        )
        status = Status.objects.get(name="Active")
        namespace = Namespace.objects.get(name="Global")
        Prefix.objects.create(prefix="2001:db8:abcd:12::/64", namespace=namespace, type="Pool", status=status)
        ip_addresses = (
            IPAddress.objects.create(address="2001:db8:abcd:12::1/128", namespace=namespace, status=status),
            IPAddress.objects.create(address="2001:db8:abcd:12::2/128", namespace=namespace, status=status),
            IPAddress.objects.create(address="2001:db8:abcd:12::3/128", namespace=namespace, status=status),
        )

        AAAARecord.objects.create(
            name="primary",
            address=ip_addresses[0],
            zone=zone,
        )
        AAAARecord.objects.create(
            name="primary",
            address=ip_addresses[1],
            zone=zone,
        )
        AAAARecord.objects.create(
            name="primary",
            address=ip_addresses[2],
            zone=zone,
        )

        cls.form_data = {
            "name": "test record",
            "address": ip_addresses[0].pk,
            "ttl": 3600,
            "zone": zone.pk,
        }

        cls.csv_data = (
            "name,address,zone",
            f"Test 3,{ip_addresses[0].pk},{zone.name}",
        )

        cls.bulk_edit_data = {"description": "Bulk edit views"}

    def helper_for_ipaddress_detail_view_side_panel(self, show_panel: str, when_not_present: bool, when_present: bool):
        """Test IP Address side panel for AAAA Records."""
        namespace = Namespace.objects.get(name="Global")
        status = Status.objects.get(name="Active")
        address = IPAddress.objects.create(address="2001:db8:abcd:12::251/64", status=status, namespace=namespace)
        other_address = IPAddress.objects.create(address="2001:db8:abcd:12::252/64", status=status, namespace=namespace)
        zone = DNSZone.objects.get(name="example_one.com")
        constance_config.nautobot_dns_models__SHOW_FORWARD_PANEL = show_panel

        # Base HTTP test to IP detail view
        url = reverse("ipam:ipaddress", args=(address.pk,))
        response = self.client.get(url)
        self.assertHttpStatus(response, 200)
        content = extract_page_body(response.content.decode(response.charset))

        # Assert AAAA Record pane when AAAA Record is not present
        self.assertInHTML("<strong>AAAA Records</strong>", content, int(when_not_present))
        component = "— No AAAA Records found —"
        self.assertInHTML(component, content, int(when_not_present))

        # Create AAAA Record and refresh page content
        aaaa_record = AAAARecord.objects.create(name="one", zone=zone, address=address)
        response = self.client.get(url)
        self.assertHttpStatus(response, 200)
        content = extract_page_body(response.content.decode(response.charset))

        # Assert AAAA Record pane when AAAA Record is present
        self.assertInHTML("<strong>AAAA Records</strong>", content, int(when_present))
        aaaarecord_url = reverse("plugins:nautobot_dns_models:aaaarecord", args=(aaaa_record.pk,))
        component = f'<a href="{aaaarecord_url}">{aaaa_record.name}</a>'
        self.assertInHTML(component, content, int(when_present))

        # Create irrelevant AAAA Record and verify it is not shown
        other_aaaa_record = AAAARecord.objects.create(name="other", zone=zone, address=other_address)
        other_aaaarecord_url = reverse("plugins:nautobot_dns_models:aaaarecord", args=(other_aaaa_record.pk,))
        other_component = f'<a href="{other_aaaarecord_url}">{other_aaaa_record.name}</a>'
        self.assertInHTML(other_component, content, 0)

    @override_settings(EXEMPT_VIEW_PERMISSIONS=["*"])
    def test_ipaddress_detail_view_side_panel_always(self):
        """Test IP Address side panel for AAAA Records when set to 'Always'."""
        self.helper_for_ipaddress_detail_view_side_panel(show_panel="always", when_not_present=True, when_present=True)

    @override_settings(EXEMPT_VIEW_PERMISSIONS=["*"])
    def test_ipaddress_detail_view_side_panel_present(self):
        """Test IP Address side panel for AAAA Records when set to 'If present'."""
        self.helper_for_ipaddress_detail_view_side_panel(
            show_panel="if_present", when_not_present=False, when_present=True
        )

    @override_settings(EXEMPT_VIEW_PERMISSIONS=["*"])
    def test_ipaddress_detail_view_side_panel_never(self):
        """Test IP Address side panel for AAAA Records when set to 'Never'."""
        self.helper_for_ipaddress_detail_view_side_panel(show_panel="never", when_not_present=False, when_present=False)


class CNAMERecordViewTest(ViewTestCases.PrimaryObjectViewTestCase):
    # pylint: disable=too-many-ancestors
    """Test the CNAMERecord views."""

    model = CNAMERecord

    @classmethod
    def setUpTestData(cls):
        zone = DNSZone.objects.create(
            name="example.com",
        )

        CNAMERecord.objects.create(
            name="www.example.com",
            alias="www.example.com",
            zone=zone,
        )
        CNAMERecord.objects.create(
            name="mail.example.com",
            alias="mail.example.com",
            zone=zone,
        )
        CNAMERecord.objects.create(
            name="blog.example.com",
            alias="blog.example.com",
            zone=zone,
        )

        cls.form_data = {
            "name": "test record",
            "alias": "test.example.com",
            "ttl": 3600,
            "zone": zone.pk,
        }

        cls.csv_data = (
            "name,alias,zone",
            f"Test 3,test2.example.com,{zone.name}",
        )

        cls.bulk_edit_data = {"description": "Bulk edit views"}


class MXRecordViewTest(ViewTestCases.PrimaryObjectViewTestCase):
    # pylint: disable=too-many-ancestors
    """Test the MXRecord views."""

    model = MXRecord

    @classmethod
    def setUpTestData(cls):
        zone = DNSZone.objects.create(
            name="example.com",
        )

        MXRecord.objects.create(
            name="mail-record-01",
            mail_server="mail01.example.com",
            zone=zone,
        )
        MXRecord.objects.create(
            name="mail-record-02",
            mail_server="mail02.example.com",
            zone=zone,
        )
        MXRecord.objects.create(
            name="mail-record-03",
            mail_server="mail03.example.com",
            zone=zone,
        )

        cls.form_data = {
            "name": "test record",
            "mail_server": "test_mail.example.com",
            "preference": 10,
            "ttl": 3600,
            "zone": zone.pk,
        }

        cls.csv_data = (
            "name,mail_server,zone",
            f"Test 3,test_mail2.example.com,{zone.name}",
        )

        cls.bulk_edit_data = {"description": "Bulk edit views"}


class TXTRecordViewTest(ViewTestCases.PrimaryObjectViewTestCase):
    # pylint: disable=too-many-ancestors
    """Test the TXTRecord views."""

    model = TXTRecord

    @classmethod
    def setUpTestData(cls):
        zone = DNSZone.objects.create(
            name="example.com",
        )

        TXTRecord.objects.create(
            name="txt-record-01",
            text="txt-record-01",
            zone=zone,
        )

        TXTRecord.objects.create(
            name="txt-record-02",
            text="txt-record-02",
            zone=zone,
        )
        TXTRecord.objects.create(
            name="txt-record-03",
            text="txt-record-03",
            zone=zone,
        )

        cls.form_data = {
            "name": "test record",
            "text": "test-text",
            "ttl": 3600,
            "zone": zone.pk,
        }

        cls.csv_data = (
            "name,text,zone",
            f"Test 3,test-text,{zone.name}",
        )

        cls.bulk_edit_data = {"description": "Bulk edit views"}


class PTRRecordViewTest(ViewTestCases.PrimaryObjectViewTestCase):
    # pylint: disable=too-many-ancestors, too-many-locals
    """Test the PTRRecord views."""

    model = PTRRecord

    @classmethod
    def setUpTestData(cls):
        zone = DNSZone.objects.create(
            name="example.com",
        )

        PTRRecord.objects.create(
            name="ptr-record-01",
            ptrdname="ptr-record-01",
            zone=zone,
        )
        PTRRecord.objects.create(
            name="ptr-record-02",
            ptrdname="ptr-record-02",
            zone=zone,
        )
        PTRRecord.objects.create(
            name="ptr-record-03",
            ptrdname="ptr-record-03",
            zone=zone,
        )

        cls.form_data = {
            "name": "test record",
            "ptrdname": "ptr-test-record",
            "ttl": 3600,
            "zone": zone.pk,
        }

        cls.csv_data = (
            "name,ptrdname,zone",
            f"Test 3,ptr-test02-record,{zone.name}",
        )

        cls.bulk_edit_data = {"description": "Bulk edit views"}

    def helper_for_ipaddress_detail_view_side_panel(self, show_panel: str, when_not_present: bool, when_present: bool):
        """Test IP Address side panel for PTR Records."""
        namespace = Namespace.objects.get(name="Global")
        type_ = PrefixTypeChoices.TYPE_POOL
        status = Status.objects.get(name="Active")
        Prefix.objects.create(prefix="192.0.2.240/29", namespace=namespace, type=type_, status=status)
        address = IPAddress.objects.create(address="192.0.2.241/29", status=status, namespace=namespace)
        other_address = IPAddress.objects.create(address="192.0.2.242/29", status=status, namespace=namespace)
        zone = DNSZone.objects.get(name="example.com")
        constance_config.nautobot_dns_models__SHOW_REVERSE_PANEL = show_panel

        # Base HTTP test to IP detail view
        url = reverse("ipam:ipaddress", args=(address.pk,))
        response = self.client.get(url)
        self.assertHttpStatus(response, 200)
        content = extract_page_body(response.content.decode(response.charset))

        # Assert PTR Record pane when PTR Record is not present
        self.assertInHTML("<strong>PTR Records</strong>", content, int(when_not_present))
        component = "— No PTR Records found —"
        self.assertInHTML(component, content, int(when_not_present))

        # Create PTR Record and refresh page content
        ptr_record = PTRRecord.objects.create(
            name="one.example.com", zone=zone, ptrdname=ipaddress_address(address.host, "reverse_pointer")
        )
        response = self.client.get(url)
        self.assertHttpStatus(response, 200)
        content = extract_page_body(response.content.decode(response.charset))

        # Assert PTR Record pane when PTR Record is present
        self.assertInHTML("<strong>PTR Records</strong>", content, int(when_present))
        ptrrecord_url = reverse("plugins:nautobot_dns_models:ptrrecord", args=(ptr_record.pk,))
        component = f'<a href="{ptrrecord_url}">{ptr_record.name}</a>'
        self.assertInHTML(component, content, int(when_present))

        # Create irrelevant PTR Record and verify it is not shown
        other_ptr_record = PTRRecord.objects.create(
            name="other.example.com", zone=zone, ptrdname=ipaddress_address(other_address.host, "reverse_pointer")
        )
        other_ptrrecord_url = reverse("plugins:nautobot_dns_models:ptrrecord", args=(other_ptr_record.pk,))
        other_component = f'<a href="{other_ptrrecord_url}">{other_ptr_record.name}</a>'
        self.assertInHTML(other_component, content, 0)

    @override_settings(EXEMPT_VIEW_PERMISSIONS=["*"])
    def test_ipaddress_detail_view_side_panel_always(self):
        """Test IP Address side panel for PTR Records when set to 'Always'."""
        self.helper_for_ipaddress_detail_view_side_panel(show_panel="always", when_not_present=True, when_present=True)

    @override_settings(EXEMPT_VIEW_PERMISSIONS=["*"])
    def test_ipaddress_detail_view_side_panel_present(self):
        """Test IP Address side panel for PTR Records when set to 'If present'."""
        self.helper_for_ipaddress_detail_view_side_panel(
            show_panel="if_present", when_not_present=False, when_present=True
        )

    @override_settings(EXEMPT_VIEW_PERMISSIONS=["*"])
    def test_ipaddress_detail_view_side_panel_never(self):
        """Test IP Address side panel for PTR Records when set to 'Never'."""
        self.helper_for_ipaddress_detail_view_side_panel(show_panel="never", when_not_present=False, when_present=False)


class SRVRecordViewTest(ViewTestCases.PrimaryObjectViewTestCase):
    # pylint: disable=too-many-ancestors
    """Test the SRVRecord views."""

    model = SRVRecord

    @classmethod
    def setUpTestData(cls):
        zone = DNSZone.objects.create(
            name="example.com",
        )

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
            name="_sip._tcp",
            priority=30,
            weight=15,
            port=5060,
            target="sip3.example.com",
            zone=zone,
        )

        cls.form_data = {
            "name": "_xmpp._tcp",
            "priority": 10,
            "weight": 5,
            "port": 5222,
            "target": "xmpp.example.com",
            "ttl": 3600,
            "zone": zone.pk,
        }

        cls.csv_data = (
            "name,priority,weight,port,target,zone",
            f"_ldap._tcp,20,10,389,ldap.example.com,{zone.name}",
        )

        cls.bulk_edit_data = {"description": "Bulk edit views"}
