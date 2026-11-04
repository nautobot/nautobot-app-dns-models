"""Unit tests for views."""

import re

from constance import config as constance_config
from django.apps import apps
from django.contrib.auth import get_user_model
from django.test import override_settings
from django.urls import reverse
from nautobot.apps.testing import TestCase, ViewTestCases
from nautobot.core.testing.utils import extract_page_body
from nautobot.extras.models import Status
from nautobot.ipam.models import IPAddress, Namespace, Prefix
from netutils.ip import ipaddress_address

from nautobot_dns_models.choices import DNSZoneTypeChoices
from nautobot_dns_models.forms import DNSZoneBulkEditForm
from nautobot_dns_models.models import (
    AAAARecord,
    ARecord,
    CNAMERecord,
    DNSRecord,
    DNSRegistrar,
    DNSView,
    DNSZone,
    MXRecord,
    NSRecord,
    PTRRecord,
    SRVRecord,
    TXTRecord,
)
from nautobot_dns_models.tests.test_models import create_zone

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


class DNSRegistrarViewTest(ViewTestCases.PrimaryObjectViewTestCase):
    """Test the DNSRegistrar views."""

    model = DNSRegistrar

    @classmethod
    def setUpTestData(cls):
        DNSRegistrar.objects.create(
            name="Registrar 1", portal_url="https://registrar1.example", account_number="ACC-001"
        )
        DNSRegistrar.objects.create(
            name="Registrar 2", portal_url="https://registrar2.example", account_number="ACC-002"
        )
        DNSRegistrar.objects.create(
            name="Registrar 3", portal_url="https://registrar3.example", account_number="ACC-003"
        )

        cls.form_data = {
            "name": "Registrar Test",
            "portal_url": "https://registrar-test.example",
            "account_number": "ACC-TEST",
        }

        cls.csv_data = (
            "name,portal_url,account_number",
            "Registrar CSV,https://registrar-csv.example,ACC-CSV",
        )

        cls.bulk_edit_data = {"account_number": "UPDATED-ACCOUNT"}


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
            "type": DNSZoneTypeChoices.TYPE_PRIMARY,
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
            "enabled": True,
        }

        cls.csv_data = (
            "name, dns_view, ttl, description, filename, soa_mname, soa_rname, soa_refresh, soa_retry, soa_expire, soa_serial, soa_minimum",
            f"Test 3, {dns_view.id}, 3600, Description 3, filename 3, auth-server, admin@example_three.com, 86400, 7200, 3600000, 0, 172800",
        )

        cls.bulk_edit_data = {
            "description": "Bulk edit views",
            "enabled": False,
            # DNSZone.soa_rname accepts a DNS-style mailbox, not only an email address
            "soa_rname": "admin.example.com",
        }


@override_settings(EXEMPT_VIEW_PERMISSIONS=["*"])
class ZoneDetailViewByZoneTypeTest(TestCase):
    """Tests for the panels and buttons a zone's detail page offers, which vary by zone type."""

    RECORD_PANELS = frozenset(
        model._meta.verbose_name_plural.upper() for model in apps.get_models() if issubclass(model, DNSRecord)
    )

    @classmethod
    def setUpTestData(cls):
        cls.catalog_zone = create_zone("catalog.example", type=DNSZoneTypeChoices.TYPE_CATALOG)
        cls.primary_zone = create_zone("primary.example")
        cls.primary_zone_record = TXTRecord(name="txt", text="a user record", zone=cls.primary_zone)
        cls.primary_zone_record.validated_save()

    def test_primary_zone_offers_every_record_panel(self):
        """An ordinary zone's detail page lists a panel for every record type."""
        self.assertLessEqual(self.RECORD_PANELS, self._panel_headings(self.primary_zone))

    def test_catalog_zone_keeps_only_the_record_panels_it_has_records_for(self):
        """A catalog zone lists only the NS and TXT panels, the record types it holds."""
        self.assertEqual(self.RECORD_PANELS & self._panel_headings(self.catalog_zone), {"NS RECORDS", "TXT RECORDS"})

    def test_catalog_zone_shows_the_version_record(self):
        """A catalog zone links the schema version TXT it auto-creates (RFC 9432 §4.2.1)."""
        record = TXTRecord.objects.get(zone=self.catalog_zone)
        self.assertIn(record.get_absolute_url(), self._detail(self.catalog_zone))

    def test_catalog_zone_shows_the_apex_ns_record(self):
        """A catalog zone links the apex NS record it auto-creates (RFC 9432 §4)."""
        record = NSRecord.objects.get(zone=self.catalog_zone)
        self.assertIn(record.get_absolute_url(), self._detail(self.catalog_zone))

    def test_catalog_zone_offers_no_write_controls_for_the_version_record(self):
        """With `change_txtrecord`, the version TXT still renders no edit link."""
        self.add_permissions("nautobot_dns_models.change_txtrecord")
        record = TXTRecord.objects.get(zone=self.catalog_zone)
        url = reverse("plugins:nautobot_dns_models:txtrecord_edit", args=(record.pk,))
        self.assertNotIn(url, self._detail(self.catalog_zone))

    def test_catalog_zone_offers_no_write_controls_for_the_apex_ns_record(self):
        """With `change_nsrecord`, the apex NS still renders no edit link."""
        self.add_permissions("nautobot_dns_models.change_nsrecord")
        record = NSRecord.objects.get(zone=self.catalog_zone)
        url = reverse("plugins:nautobot_dns_models:nsrecord_edit", args=(record.pk,))
        self.assertNotIn(url, self._detail(self.catalog_zone))

    def test_primary_zone_keeps_write_controls_for_its_records(self):
        """With `change_txtrecord`, an ordinary zone's TXT record still renders its edit link."""
        self.add_permissions("nautobot_dns_models.change_txtrecord")
        url = reverse("plugins:nautobot_dns_models:txtrecord_edit", args=(self.primary_zone_record.pk,))
        self.assertIn(url, self._detail(self.primary_zone))

    def test_catalog_zone_offers_no_add_button_for_records(self):
        """With `add_txtrecord`, a catalog zone's TXT panel renders no Add button."""
        self.add_permissions("nautobot_dns_models.add_txtrecord")
        url = reverse("plugins:nautobot_dns_models:txtrecord_add")
        self.assertNotIn(url, self._detail(self.catalog_zone))

    def test_primary_zone_keeps_the_add_button_on_its_record_panels(self):
        """With `add_txtrecord`, an ordinary zone's TXT panel still renders its Add button."""
        self.add_permissions("nautobot_dns_models.add_txtrecord")
        url = reverse("plugins:nautobot_dns_models:txtrecord_add")
        self.assertIn(url, self._detail(self.primary_zone))

    def test_catalog_zone_hides_the_add_records_menu(self):
        """With `add_arecord`, a catalog zone renders no Add Records dropdown."""
        self.add_permissions("nautobot_dns_models.change_dnszone", "nautobot_dns_models.add_arecord")
        self.assertNotIn("Add Records", self._detail(self.catalog_zone))

    def test_primary_zone_keeps_the_add_records_menu(self):
        """With `add_arecord`, an ordinary zone still renders the Add Records dropdown."""
        self.add_permissions("nautobot_dns_models.change_dnszone", "nautobot_dns_models.add_arecord")
        self.assertIn("Add Records", self._detail(self.primary_zone))

    def test_catalog_zone_has_no_record_statistics(self):
        """A catalog zone renders no Records Statistics panel, holding no user records to count."""
        self.assertNotIn("RECORDS STATISTICS", self._panel_headings(self.catalog_zone))

    def test_catalog_zone_has_no_registration_panel(self):
        """A catalog zone renders no Registration panel, not being a registered name."""
        self.assertNotIn("REGISTRATION", self._panel_headings(self.catalog_zone))

    def test_primary_zone_keeps_the_registration_panel(self):
        """An ordinary zone still renders the Registration panel."""
        self.assertIn("REGISTRATION", self._panel_headings(self.primary_zone))

    def test_primary_zone_keeps_record_statistics(self):
        """An ordinary zone still renders the Records Statistics panel."""
        self.assertIn("RECORDS STATISTICS", self._panel_headings(self.primary_zone))

    def _detail(self, zone):
        """Return the rendered body of `zone`'s detail page."""
        response = self.client.get(zone.get_absolute_url())
        self.assertHttpStatus(response, 200)
        return extract_page_body(response.content.decode(response.charset))

    def _panel_headings(self, zone):
        """Return the panel headings on `zone`'s detail page, upper-cased since Nautobot's own casing varies.

        Headings rather than raw page text: a hidden panel's title survives elsewhere in the markup, in
        the table configuration drawer and the navigation menu, so a substring search sees it either way.
        """
        return {label.upper() for label in re.findall(r"<strong>([^<]*)</strong>", self._detail(zone))}


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
            "enabled": True,
        }

        cls.csv_data = (
            "name,server,zone, ttl",
            f"Test 3,server 3,{zone.name}, 3600",
        )

        cls.bulk_edit_data = {"description": "Bulk edit views", "enabled": False}


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
            "enabled": True,
        }

        cls.csv_data = (
            "name,ip_address,zone",
            f"Test 3,{cls.ip_addresses[0].pk},{zone.name}",
        )

        cls.bulk_edit_data = {"description": "Bulk edit views", "enabled": False}

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
            "enabled": True,
        }

        cls.csv_data = (
            "name,ip_address,zone",
            f"Test 3,{cls.ip_addresses[0].pk},{zone.name}",
        )

        cls.bulk_edit_data = {"description": "Bulk edit views", "enabled": False}

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
            "enabled": True,
        }

        cls.csv_data = (
            "name,alias,zone",
            f"Test 3,test2.example.com,{zone.name}",
        )

        cls.bulk_edit_data = {"description": "Bulk edit views", "enabled": False}


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
            "enabled": True,
        }

        cls.csv_data = (
            "name,mail_server,zone",
            f"Test 3,test_mail2.example.com,{zone.name}",
        )

        cls.bulk_edit_data = {"description": "Bulk edit views", "enabled": False}


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
            "enabled": True,
        }

        cls.csv_data = (
            "name,text,zone",
            f"Test 3,test-text,{zone.name}",
            # A 2048-bit DKIM key: CSV import still resolves the natural key with `text` far past the
            # former 256-character limit.
            f"Test 4,v=DKIM1; k=rsa; p={'A' * 582},{zone.name}",
        )

        cls.bulk_edit_data = {"description": "Bulk edit views", "enabled": False}


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
            "enabled": True,
        }

        cls.csv_data = (
            "name,ptrdname,zone",
            f"Test 3,ptr-test02-record,{zone.name}",
        )

        cls.bulk_edit_data = {"description": "Bulk edit views", "enabled": False}

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
            "enabled": True,
        }

        cls.csv_data = (
            "name,priority,weight,port,target,zone",
            f"_ldap._tcp,20,10,389,ldap.example.com,{zone.name}",
        )

        cls.bulk_edit_data = {"description": "Bulk edit views", "enabled": False}


class ZoneBulkEditPTRControlTest(TestCase):
    """Tests that a bulk edit withdraws the PTR control once a catalog zone is among the selection.

    A catalog zone refuses `auto_create_ptr`, and the bulk edit job saves each object in turn outside
    a transaction, so offering the control would write the primary zones and then fail on the first
    catalog zone.
    """

    WITHDRAWN = "Catalog zones cannot enable this, and the selection includes one."

    @classmethod
    def setUpTestData(cls):
        cls.catalog_zone = create_zone("bulk-catalog.example", type=DNSZoneTypeChoices.TYPE_CATALOG)
        cls.primary_zones = [create_zone(f"bulk-primary-{index}.example") for index in range(2)]
        cls.bulk_edit_path = reverse("plugins:nautobot_dns_models:dnszone_bulk_edit")

    def setUp(self):
        """Grant the permissions a bulk edit needs before its selection is judged."""
        super().setUp()
        self.add_permissions("nautobot_dns_models.view_dnszone", "nautobot_dns_models.change_dnszone")

    def test_a_selection_of_primary_zones_offers_the_control(self):
        """A selection of primary zones renders the `auto_create_ptr` control."""
        content = self._bulk_edit_form(pk_list=[zone.pk for zone in self.primary_zones])
        self.assertIn('name="auto_create_ptr"', content)
        self.assertNotIn(self.WITHDRAWN, content)

    def test_a_selection_holding_a_catalog_zone_withdraws_the_control(self):
        """One catalog zone among primary zones withdraws the control for the whole selection."""
        content = self._bulk_edit_form(pk_list=[self.primary_zones[0].pk, self.catalog_zone.pk])
        self.assertIn(self.WITHDRAWN, content)

    def test_select_all_withdraws_the_control_when_it_includes_a_catalog_zone(self):
        """An unfiltered "select all" withdraws the control, resolving to every zone including the catalog zone."""
        self.assertIn(self.WITHDRAWN, self._bulk_edit_form(edit_all=True))

    def test_select_all_keeps_the_control_when_filtered_to_primary_zones(self):
        """With `?type=primary`, "select all" resolves to primary zones alone and keeps the control."""
        content = self._bulk_edit_form(edit_all=True, query=f"?type={DNSZoneTypeChoices.TYPE_PRIMARY}")
        self.assertIn('name="auto_create_ptr"', content)
        self.assertNotIn(self.WITHDRAWN, content)

    def test_a_withdrawn_control_discards_a_submitted_value(self):
        """A disabled `auto_create_ptr` cleans to None, so a submitted value never reaches the job."""
        form = DNSZoneBulkEditForm(
            DNSZone,
            {"pk": [str(zone.pk) for zone in self.primary_zones], "auto_create_ptr": "True"},
            selection=DNSZone.objects.filter(pk__in=[self.primary_zones[0].pk, self.catalog_zone.pk]),
        )
        self.assertTrue(form.is_valid(), form.errors)
        self.assertIsNone(form.cleaned_data["auto_create_ptr"])

    def _bulk_edit_form(self, pk_list=None, edit_all=False, query=""):
        """Return the bulk edit page rendered for a selection, named by pk or claimed wholesale."""
        data = {"pk": [str(pk) for pk in pk_list or []]}
        if edit_all:
            data["_all"] = "on"

        response = self.client.post(f"{self.bulk_edit_path}{query}", data)
        self.assertHttpStatus(response, 200)
        return extract_page_body(response.content.decode(response.charset))
