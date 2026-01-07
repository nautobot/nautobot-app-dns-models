"""Unit tests for views."""

from constance import config as constance_config
from django.contrib.auth import get_user_model
from django.test import override_settings
from django.urls import reverse
from nautobot.apps.testing import ViewTestCases
from nautobot.core.testing.utils import extract_page_body
from nautobot.extras.models import Status
from nautobot.ipam.models import IPAddress, Namespace, Prefix
from netutils.ip import ipaddress_address

from nautobot_dns_models.models import (
    AAAARecord,
    ARecord,
    CNAMERecord,
    DNSView,
    DNSZone,
    MXRecord,
    NSRecord,
    PTRRecord,
    SRVRecord,
    TXTRecord,
)

User = get_user_model()


class SidePanelTestsMixin:
    """Provide test methods for template_content side panels."""

    def detail_view_test_side_panels(
        self, detail_object, render_panel, panel_model, panel_objects=None, panel_title=None
    ):  # pylint: disable=too-many-arguments
        """Test whether a side panel renders properly.

        Args:
            detail_object (obj): The object with the under-test detailed view.
            render_panel (bool): Should the under-test side panel render or not.
            panel_model (obj): The class of the objects in the side panel.
            panel_objects (list, optional): List of expected panel objects.
            panel_title (str, optional): The title of the side panel, defaults to panel_model._meta.verbose_name_plural.
        """
        panel_objects = panel_objects or []
        panel_title = panel_title or panel_model._meta.verbose_name_plural

        detail_reverse = f"{detail_object._meta.app_label}:{detail_object._meta.model_name}"
        url = reverse(detail_reverse, args=(detail_object.pk,))
        response = self.client.get(url)
        self.assertHttpStatus(response, 200)
        content = extract_page_body(response.content.decode(response.charset))

        self.assertInHTML(f"<strong>{panel_title}</strong>", content, int(render_panel))
        if render_panel:
            if not panel_objects:
                component = f"— No {panel_model._meta.verbose_name_plural} found —"
                self.assertInHTML(component, content, 1)
            for panel_object in panel_objects:
                panel_reverse = f"plugins:{panel_object._meta.app_label}:{panel_object._meta.model_name}"
                panel_object_url = reverse(panel_reverse, args=(panel_object.pk,))
                component = f'<a href="{panel_object_url}">{panel_object.name}</a>'
                self.assertInHTML(component, content, 1)


class DNSViewViewTest(ViewTestCases.PrimaryObjectViewTestCase):
    """Test the DNSView views."""

    model = DNSView

    @classmethod
    def setUpTestData(cls):
        DNSView.objects.create(
            name="View 1",
            description="Test Description",
        )
        DNSView.objects.create(
            name="View 2",
            description="Test Description",
        )
        DNSView.objects.create(
            name="View 3",
            description="Test Description",
        )

        cls.form_data = {
            "name": "Test 1",
            "description": "Initial model",
        }

        cls.csv_data = (
            "name,description",
            "Test 3,Description 3",
        )

        cls.bulk_edit_data = {"description": "Bulk edit views"}


class DnsZoneViewTest(ViewTestCases.PrimaryObjectViewTestCase):
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

        dns_view = DNSView.objects.get(name="Default")
        cls.form_data = {
            "name": "Test 1",
            "dns_view": dns_view.id,
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
            "name, dns_view, ttl, description, filename, soa_mname, soa_rname, soa_refresh, soa_retry, soa_expire, soa_serial, soa_minimum",
            f"Test 3, {dns_view.id}, 3600, Description 3, filename 3, auth-server, admin@example_three.com, 86400, 7200, 3600000, 0, 172800",
        )

        cls.bulk_edit_data = {"description": "Bulk edit views"}


class NSRecordViewTest(ViewTestCases.PrimaryObjectViewTestCase):
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


class ARecordViewTest(ViewTestCases.PrimaryObjectViewTestCase, SidePanelTestsMixin):
    # pylint: disable=too-many-ancestors
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
        cls.ip_addresses = (
            IPAddress.objects.create(address="10.0.0.1/32", namespace=namespace, status=status),
            IPAddress.objects.create(address="10.0.0.2/32", namespace=namespace, status=status),
            IPAddress.objects.create(address="10.0.0.3/32", namespace=namespace, status=status),
        )
        cls.ip_addresses_wo_records = (
            IPAddress.objects.create(address="10.0.0.4/32", namespace=namespace, status=status),
        )

        ARecord.objects.create(
            name="primary",
            ip_address=cls.ip_addresses[0],
            zone=zone,
        )
        ARecord.objects.create(
            name="primary",
            ip_address=cls.ip_addresses[1],
            zone=zone,
        )
        ARecord.objects.create(
            name="primary",
            ip_address=cls.ip_addresses[2],
            zone=zone,
        )

        cls.form_data = {
            "name": "test record",
            "ip_address": cls.ip_addresses[0].pk,
            "ttl": 3600,
            "zone": zone.pk,
        }

        cls.csv_data = (
            "name,ip_address,zone",
            f"Test 3,{cls.ip_addresses[0].pk},{zone.name}",
        )

        cls.bulk_edit_data = {"description": "Bulk edit views"}

    @override_settings(EXEMPT_VIEW_PERMISSIONS=["*"])
    def test_ipaddress_detail_view_side_panel_always(self):
        """Test IP Address side panel for A Records when set to 'Always'."""
        constance_config.nautobot_dns_models__SHOW_FORWARD_PANEL = "always"

        address = self.ip_addresses_wo_records[0]
        self.detail_view_test_side_panels(
            detail_object=address, render_panel=True, panel_model=ARecord, panel_objects=[]
        )

        address = self.ip_addresses[0]
        arecord = ARecord.objects.get(ip_address=address)
        self.detail_view_test_side_panels(
            detail_object=address, render_panel=True, panel_model=ARecord, panel_objects=[arecord]
        )

    @override_settings(EXEMPT_VIEW_PERMISSIONS=["*"])
    def test_ipaddress_detail_view_side_panel_present(self):
        """Test IP Address side panel for A Records when set to 'If present'."""
        constance_config.nautobot_dns_models__SHOW_FORWARD_PANEL = "if_present"

        address = self.ip_addresses_wo_records[0]
        self.detail_view_test_side_panels(
            detail_object=address, render_panel=False, panel_model=ARecord, panel_objects=[]
        )

        address = self.ip_addresses[0]
        arecord = ARecord.objects.get(ip_address=address)
        self.detail_view_test_side_panels(
            detail_object=address, render_panel=True, panel_model=ARecord, panel_objects=[arecord]
        )

    @override_settings(EXEMPT_VIEW_PERMISSIONS=["*"])
    def test_ipaddress_detail_view_side_panel_never(self):
        """Test IP Address side panel for A Records when set to 'Never'."""
        constance_config.nautobot_dns_models__SHOW_FORWARD_PANEL = "never"

        address = self.ip_addresses_wo_records[0]
        self.detail_view_test_side_panels(
            detail_object=address, render_panel=False, panel_model=ARecord, panel_objects=[]
        )

        address = self.ip_addresses[0]
        arecord = ARecord.objects.get(ip_address=address)
        self.detail_view_test_side_panels(
            detail_object=address, render_panel=False, panel_model=ARecord, panel_objects=[arecord]
        )


class AAAARecordViewTest(ViewTestCases.PrimaryObjectViewTestCase, SidePanelTestsMixin):
    # pylint: disable=too-many-ancestors
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
        cls.ip_addresses = (
            IPAddress.objects.create(address="2001:db8:abcd:12::1/128", namespace=namespace, status=status),
            IPAddress.objects.create(address="2001:db8:abcd:12::2/128", namespace=namespace, status=status),
            IPAddress.objects.create(address="2001:db8:abcd:12::3/128", namespace=namespace, status=status),
        )
        cls.ip_addresses_wo_records = (
            IPAddress.objects.create(address="2001:db8:abcd:12::4/128", namespace=namespace, status=status),
        )

        AAAARecord.objects.create(
            name="primary",
            ip_address=cls.ip_addresses[0],
            zone=zone,
        )
        AAAARecord.objects.create(
            name="primary",
            ip_address=cls.ip_addresses[1],
            zone=zone,
        )
        AAAARecord.objects.create(
            name="primary",
            ip_address=cls.ip_addresses[2],
            zone=zone,
        )

        cls.form_data = {
            "name": "test record",
            "ip_address": cls.ip_addresses[0].pk,
            "ttl": 3600,
            "zone": zone.pk,
        }

        cls.csv_data = (
            "name,ip_address,zone",
            f"Test 3,{cls.ip_addresses[0].pk},{zone.name}",
        )

        cls.bulk_edit_data = {"description": "Bulk edit views"}

    @override_settings(EXEMPT_VIEW_PERMISSIONS=["*"])
    def test_ipaddress_detail_view_side_panel_always(self):
        """Test IP Address side panel for AAAA Records when set to 'Always'."""
        constance_config.nautobot_dns_models__SHOW_FORWARD_PANEL = "always"

        address = self.ip_addresses_wo_records[0]
        self.detail_view_test_side_panels(
            detail_object=address, render_panel=True, panel_model=AAAARecord, panel_objects=[]
        )

        address = self.ip_addresses[0]
        aaaarecord = AAAARecord.objects.get(ip_address=address)
        self.detail_view_test_side_panels(
            detail_object=address, render_panel=True, panel_model=AAAARecord, panel_objects=[aaaarecord]
        )

    @override_settings(EXEMPT_VIEW_PERMISSIONS=["*"])
    def test_ipaddress_detail_view_side_panel_present(self):
        """Test IP Address side panel for AAAA Records when set to 'If present'."""
        constance_config.nautobot_dns_models__SHOW_FORWARD_PANEL = "if_present"

        address = self.ip_addresses_wo_records[0]
        self.detail_view_test_side_panels(
            detail_object=address, render_panel=False, panel_model=AAAARecord, panel_objects=[]
        )

        address = self.ip_addresses[0]
        aaaarecord = AAAARecord.objects.get(ip_address=address)
        self.detail_view_test_side_panels(
            detail_object=address, render_panel=True, panel_model=AAAARecord, panel_objects=[aaaarecord]
        )

    @override_settings(EXEMPT_VIEW_PERMISSIONS=["*"])
    def test_ipaddress_detail_view_side_panel_never(self):
        """Test IP Address side panel for AAAA Records when set to 'Never'."""
        constance_config.nautobot_dns_models__SHOW_FORWARD_PANEL = "never"

        address = self.ip_addresses_wo_records[0]
        self.detail_view_test_side_panels(
            detail_object=address, render_panel=False, panel_model=AAAARecord, panel_objects=[]
        )

        address = self.ip_addresses[0]
        aaaarecord = AAAARecord.objects.get(ip_address=address)
        self.detail_view_test_side_panels(
            detail_object=address, render_panel=False, panel_model=AAAARecord, panel_objects=[aaaarecord]
        )


class CNAMERecordViewTest(ViewTestCases.PrimaryObjectViewTestCase):
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


class PTRRecordViewTest(ViewTestCases.PrimaryObjectViewTestCase, SidePanelTestsMixin):
    # pylint: disable=too-many-ancestors
    """Test the PTRRecord views."""

    model = PTRRecord

    @classmethod
    def setUpTestData(cls):
        zone = DNSZone.objects.create(
            name="example.com",
        )
        status = Status.objects.get(name="Active")
        namespace = Namespace.objects.get(name="Global")
        Prefix.objects.create(prefix="10.0.0.0/24", namespace=namespace, type="Pool", status=status)
        cls.ip_addresses = (IPAddress.objects.create(address="10.0.0.1/32", namespace=namespace, status=status),)
        cls.ip_addresses_wo_records = (
            IPAddress.objects.create(address="10.0.0.2/32", namespace=namespace, status=status),
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

        PTRRecord.objects.create(
            name="one.example.com",
            ptrdname=ipaddress_address(cls.ip_addresses[0].host, "reverse_pointer"),
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

    @override_settings(EXEMPT_VIEW_PERMISSIONS=["*"])
    def test_ipaddress_detail_view_side_panel_always(self):
        """Test IP Address side panel for PTR Records when set to 'Always'."""
        constance_config.nautobot_dns_models__SHOW_REVERSE_PANEL = "always"

        address = self.ip_addresses_wo_records[0]
        self.detail_view_test_side_panels(
            detail_object=address, render_panel=True, panel_model=PTRRecord, panel_objects=[]
        )

        address = self.ip_addresses[0]
        ptrrecord = PTRRecord.objects.get(ptrdname=ipaddress_address(address.host, "reverse_pointer"))
        self.detail_view_test_side_panels(
            detail_object=address, render_panel=True, panel_model=PTRRecord, panel_objects=[ptrrecord]
        )

    @override_settings(EXEMPT_VIEW_PERMISSIONS=["*"])
    def test_ipaddress_detail_view_side_panel_present(self):
        """Test IP Address side panel for PTR Records when set to 'If present'."""
        constance_config.nautobot_dns_models__SHOW_REVERSE_PANEL = "if_present"

        address = self.ip_addresses_wo_records[0]
        self.detail_view_test_side_panels(
            detail_object=address, render_panel=False, panel_model=PTRRecord, panel_objects=[]
        )

        address = self.ip_addresses[0]
        ptrrecord = PTRRecord.objects.get(ptrdname=ipaddress_address(address.host, "reverse_pointer"))
        self.detail_view_test_side_panels(
            detail_object=address, render_panel=True, panel_model=PTRRecord, panel_objects=[ptrrecord]
        )

    @override_settings(EXEMPT_VIEW_PERMISSIONS=["*"])
    def test_ipaddress_detail_view_side_panel_never(self):
        """Test IP Address side panel for PTR Records when set to 'Never'."""
        constance_config.nautobot_dns_models__SHOW_REVERSE_PANEL = "never"

        address = self.ip_addresses_wo_records[0]
        self.detail_view_test_side_panels(
            detail_object=address, render_panel=False, panel_model=PTRRecord, panel_objects=[]
        )

        address = self.ip_addresses[0]
        ptrrecord = PTRRecord.objects.get(ptrdname=ipaddress_address(address.host, "reverse_pointer"))
        self.detail_view_test_side_panels(
            detail_object=address, render_panel=False, panel_model=PTRRecord, panel_objects=[ptrrecord]
        )


class SRVRecordViewTest(ViewTestCases.PrimaryObjectViewTestCase):
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
