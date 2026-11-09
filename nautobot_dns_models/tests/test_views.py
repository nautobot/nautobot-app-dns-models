"""Unit tests for views."""
# pylint: disable=too-many-lines

import re
from unittest.mock import patch

from constance import config as constance_config
from django.apps import apps
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.contrib.messages import get_messages
from django.test import override_settings
from django.urls import reverse
from nautobot.apps.testing import AssertNoRepeatedQueries, TestCase, ViewTestCases, create_job_result_and_run_job
from nautobot.core.testing.utils import extract_page_body, get_deletable_objects
from nautobot.extras.choices import JobResultStatusChoices, ObjectChangeActionChoices
from nautobot.extras.models import ObjectChange, Status
from nautobot.ipam.models import IPAddress, Namespace, Prefix
from nautobot.users.models import ObjectPermission
from netutils.ip import ipaddress_address

from nautobot_dns_models.choices import DNSZoneTypeChoices
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
from nautobot_dns_models.tests.fixtures import create_zone
from nautobot_dns_models.views import DNSZoneUIViewSet

User = get_user_model()


def permit_zone_change(user, *zones):
    """Let `user` view every zone and change only `zones`."""
    content_type = ContentType.objects.get_for_model(DNSZone)
    view_permission = ObjectPermission.objects.create(name="view zones", actions=["view"])
    view_permission.object_types.set([content_type])
    view_permission.users.add(user)
    change_permission = ObjectPermission.objects.create(
        name="change some zones", actions=["change"], constraints={"pk__in": [str(zone.pk) for zone in zones]}
    )
    change_permission.object_types.set([content_type])
    change_permission.users.add(user)


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


class DNSZoneViewTest(ViewTestCases.PrimaryObjectViewTestCase):
    """Test the DNSZone views."""

    model = DNSZone
    RECORD_PANELS = frozenset(
        record_model._meta.verbose_name_plural.upper()
        for record_model in apps.get_models()
        if issubclass(record_model, DNSRecord)
    )

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

        # The generic edit tests edit whichever zone sorts first, which may be the catalog zone,
        # and a zone's type cannot change after creation.
        cls.update_data = {key: value for key, value in cls.form_data.items() if key != "type"}

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

        cls.catalog_zone = create_zone("catalog.example", type=DNSZoneTypeChoices.TYPE_CATALOG)
        cls.primary_zone = create_zone("primary.example")
        cls.primary_zone_record = TXTRecord(name="txt", text="a user record", zone=cls.primary_zone)
        cls.primary_zone_record.validated_save()
        cls.member_zone = create_zone("member.example", catalog_zone=cls.catalog_zone)

    def get_deletable_object(self):
        """Return a deletable zone in no catalog, since deleting a member also needs change permission on its catalog."""
        instance = get_deletable_objects(self.model, self._get_queryset().filter(catalog_zone__isnull=True)).first()
        if instance is None:
            self.fail("Couldn't find a single deletable object!")
        return instance

    def _column_headers(self, zone):
        """Return the table column headers on `zone`'s detail page, upper-cased and stripped of markup."""
        cells = re.findall(r"<th\b[^>]*>(.*?)</th>", self._detail(zone), flags=re.DOTALL)
        return {re.sub(r"<[^>]+>", "", cell).strip().upper() for cell in cells}

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

    def test_custom_actions(self):
        """Each catalog action passes core's custom-action check on a zone that offers it.

        `add_member` runs against a catalog zone, `add_to_catalog` against a zone in no catalog, and
        `remove_from_catalog` against a member.
        """
        catalog_zone = create_zone("custom-actions-catalog.example", type=DNSZoneTypeChoices.TYPE_CATALOG)
        create_zone("custom-actions-member.example", catalog_zone=catalog_zone)
        cases = (
            (DNSZoneUIViewSet.add_member, DNSZone.objects.filter(type=DNSZoneTypeChoices.TYPE_CATALOG)),
            (
                DNSZoneUIViewSet.add_to_catalog,
                DNSZone.objects.filter(catalog_zone__isnull=True).exclude(type=DNSZoneTypeChoices.TYPE_CATALOG),
            ),
            (DNSZoneUIViewSet.remove_from_catalog, DNSZone.objects.filter(catalog_zone__isnull=False)),
        )
        for action_func, zones in cases:
            with (
                patch.object(DNSZoneUIViewSet, "get_extra_actions", return_value=[action_func]),
                patch.object(self, "_get_queryset", return_value=zones),
            ):
                super().test_custom_actions()

    def test_list_names_each_zone_catalog_without_per_zone_queries(self):
        """The zone list names each zone's catalog without a query per row."""
        catalog = DNSZone.objects.create(name="catalog-list.example", type=DNSZoneTypeChoices.TYPE_CATALOG)
        for index in range(12):
            DNSZone.objects.create(name=f"member-list-{index}.example", catalog_zone=catalog)

        self.add_permissions("nautobot_dns_models.view_dnszone")
        # The rows arrive on the HTMX follow-up request; the first response is an empty table shell.
        with AssertNoRepeatedQueries(self):
            response = self.client.get(self._get_url("list"), headers={"HX-Request": "true"})

        self.assertHttpStatus(response, 200)
        body = extract_page_body(response.content.decode(response.charset))
        # The catalog's own row names it once; every member row names it again in the catalog column.
        self.assertEqual(body.count(catalog.name), 13)

    @override_settings(EXEMPT_VIEW_PERMISSIONS=["*"])
    def test_primary_zone_offers_every_record_panel(self):
        """An ordinary zone's detail page lists a panel for every record type."""
        self.assertLessEqual(self.RECORD_PANELS, self._panel_headings(self.primary_zone))

    @override_settings(EXEMPT_VIEW_PERMISSIONS=["*"])
    def test_primary_zone_lists_each_record_panel_once(self):
        """An ordinary zone's detail page lists each record panel once, with no system-managed copy."""
        headings = [label.upper() for label in re.findall(r"<strong>([^<]*)</strong>", self._detail(self.primary_zone))]
        self.assertEqual(
            {heading: headings.count(heading) for heading in self.RECORD_PANELS}, dict.fromkeys(self.RECORD_PANELS, 1)
        )

    @override_settings(EXEMPT_VIEW_PERMISSIONS=["*"])
    def test_catalog_zone_keeps_only_the_record_panels_it_has_records_for(self):
        """A catalog zone lists only the NS and TXT panels, the record types it holds."""
        self.assertEqual(self.RECORD_PANELS & self._panel_headings(self.catalog_zone), {"NS RECORDS", "TXT RECORDS"})

    @override_settings(EXEMPT_VIEW_PERMISSIONS=["*"])
    def test_catalog_zone_shows_the_version_record(self):
        """A catalog zone links the schema version TXT it auto-creates (RFC 9432 §4.2.1)."""
        record = TXTRecord.objects.get(zone=self.catalog_zone)
        self.assertIn(record.get_absolute_url(), self._detail(self.catalog_zone))

    @override_settings(EXEMPT_VIEW_PERMISSIONS=["*"])
    def test_catalog_zone_shows_the_apex_ns_record(self):
        """A catalog zone links the apex NS record it auto-creates (RFC 9432 §4)."""
        record = NSRecord.objects.get(zone=self.catalog_zone)
        self.assertIn(record.get_absolute_url(), self._detail(self.catalog_zone))

    @override_settings(EXEMPT_VIEW_PERMISSIONS=["*"])
    def test_catalog_zone_offers_no_write_controls_for_the_version_record(self):
        """A catalog zone's version TXT record has no edit link, even with `change_txtrecord`."""
        self.add_permissions("nautobot_dns_models.change_txtrecord")
        record = TXTRecord.objects.get(zone=self.catalog_zone)
        url = reverse("plugins:nautobot_dns_models:txtrecord_edit", args=(record.pk,))
        self.assertNotIn(url, self._detail(self.catalog_zone))

    @override_settings(EXEMPT_VIEW_PERMISSIONS=["*"])
    def test_catalog_zone_offers_no_write_controls_for_the_apex_ns_record(self):
        """A catalog zone's apex NS record has no edit link, even with `change_nsrecord`."""
        self.add_permissions("nautobot_dns_models.change_nsrecord")
        record = NSRecord.objects.get(zone=self.catalog_zone)
        url = reverse("plugins:nautobot_dns_models:nsrecord_edit", args=(record.pk,))
        self.assertNotIn(url, self._detail(self.catalog_zone))

    @override_settings(EXEMPT_VIEW_PERMISSIONS=["*"])
    def test_primary_zone_keeps_write_controls_for_its_records(self):
        """A primary zone's TXT record has an edit link with `change_txtrecord`."""
        self.add_permissions("nautobot_dns_models.change_txtrecord")
        url = reverse("plugins:nautobot_dns_models:txtrecord_edit", args=(self.primary_zone_record.pk,))
        self.assertIn(url, self._detail(self.primary_zone))

    @override_settings(EXEMPT_VIEW_PERMISSIONS=["*"])
    def test_catalog_zone_offers_no_add_button_for_records(self):
        """A catalog zone's TXT panel has no Add button, even with `add_txtrecord`."""
        self.add_permissions("nautobot_dns_models.add_txtrecord")
        url = reverse("plugins:nautobot_dns_models:txtrecord_add")
        self.assertNotIn(url, self._detail(self.catalog_zone))

    @override_settings(EXEMPT_VIEW_PERMISSIONS=["*"])
    def test_primary_zone_keeps_the_add_button_on_its_record_panels(self):
        """A primary zone's TXT panel has an Add button with `add_txtrecord`."""
        self.add_permissions("nautobot_dns_models.add_txtrecord")
        url = reverse("plugins:nautobot_dns_models:txtrecord_add")
        self.assertIn(url, self._detail(self.primary_zone))

    @override_settings(EXEMPT_VIEW_PERMISSIONS=["*"])
    def test_catalog_zone_record_panels_have_no_comment_column(self):
        """A catalog zone's record panels have no Comment column, since its records never carry one."""
        self.assertNotIn("COMMENT", self._column_headers(self.catalog_zone))

    @override_settings(EXEMPT_VIEW_PERMISSIONS=["*"])
    def test_primary_zone_keeps_the_comment_column(self):
        """A primary zone's TXT panel has a Comment column."""
        self.assertIn("COMMENT", self._column_headers(self.primary_zone))

    @override_settings(EXEMPT_VIEW_PERMISSIONS=["*"])
    def test_catalog_zone_hides_the_add_records_menu(self):
        """A catalog zone has no Add Records menu, even with `add_arecord`."""
        self.add_permissions("nautobot_dns_models.change_dnszone", "nautobot_dns_models.add_arecord")
        self.assertNotIn("Add Records", self._detail(self.catalog_zone))

    @override_settings(EXEMPT_VIEW_PERMISSIONS=["*"])
    def test_primary_zone_keeps_the_add_records_menu(self):
        """A primary zone has the Add Records menu with `add_arecord`."""
        self.add_permissions("nautobot_dns_models.change_dnszone", "nautobot_dns_models.add_arecord")
        self.assertIn("Add Records", self._detail(self.primary_zone))

    @override_settings(EXEMPT_VIEW_PERMISSIONS=["*"])
    def test_catalog_zone_has_no_record_statistics(self):
        """A catalog zone renders no Records Statistics panel, holding no user records to count."""
        self.assertNotIn("RECORDS STATISTICS", self._panel_headings(self.catalog_zone))

    @override_settings(EXEMPT_VIEW_PERMISSIONS=["*"])
    def test_catalog_zone_has_no_registration_panel(self):
        """A catalog zone renders no Registration panel, not being a registered name."""
        self.assertNotIn("REGISTRATION", self._panel_headings(self.catalog_zone))

    @override_settings(EXEMPT_VIEW_PERMISSIONS=["*"])
    def test_primary_zone_keeps_the_registration_panel(self):
        """A primary zone has a Registration panel."""
        self.assertIn("REGISTRATION", self._panel_headings(self.primary_zone))

    @override_settings(EXEMPT_VIEW_PERMISSIONS=["*"])
    def test_primary_zone_keeps_record_statistics(self):
        """A primary zone has a Records Statistics panel."""
        self.assertIn("RECORDS STATISTICS", self._panel_headings(self.primary_zone))

    @override_settings(EXEMPT_VIEW_PERMISSIONS=["*"])
    def test_catalog_zone_lists_its_members(self):
        """A catalog zone renders a Member Zones panel carrying each member's PTR record name."""
        self.assertIn("MEMBER ZONES", self._panel_headings(self.catalog_zone))
        content = self._detail(self.catalog_zone)
        self.assertIn(self.member_zone.get_absolute_url(), content)
        self.assertIn(self.member_zone.ptr_record_name, content)

    @override_settings(EXEMPT_VIEW_PERMISSIONS=["*"])
    def test_member_zones_panel_lists_members_by_name(self):
        """The Member Zones panel lists members in name order, not the order they were added."""
        members = [create_zone(name, catalog_zone=self.catalog_zone) for name in ("c.example", "b.example")]
        members.append(self.member_zone)
        content = self._detail(self.catalog_zone)
        positions = [content.index(zone.get_absolute_url()) for zone in sorted(members, key=lambda zone: zone.name)]
        self.assertEqual(positions, sorted(positions))

    @override_settings(EXEMPT_VIEW_PERMISSIONS=["*"])
    def test_member_zones_panel_offers_edit(self):
        """The Member Zones panel links each member's edit page."""
        self.add_permissions("nautobot_dns_models.change_dnszone")
        url = reverse("plugins:nautobot_dns_models:dnszone_edit", kwargs={"pk": self.member_zone.pk})
        self.assertIn(url, self._detail(self.catalog_zone))

    @override_settings(EXEMPT_VIEW_PERMISSIONS=["*"])
    def test_member_zones_panel_links_the_catalogs_ptr_records(self):
        """The Member Zones panel links the PTR record list filtered to the catalog zone."""
        url = f"{reverse('plugins:nautobot_dns_models:ptrrecord_list')}?zone={self.catalog_zone.pk}"
        self.assertIn(url, self._detail(self.catalog_zone))

    @override_settings(EXEMPT_VIEW_PERMISSIONS=["nautobot_dns_models.dnszone"])
    def test_member_zones_panel_omits_the_ptr_record_link_without_view_ptrrecord(self):
        """The Member Zones panel has no PTR record link for a user who may not view PTR records."""
        url = f"{reverse('plugins:nautobot_dns_models:ptrrecord_list')}?zone={self.catalog_zone.pk}"
        self.assertNotIn(url, self._detail(self.catalog_zone))

    @override_settings(EXEMPT_VIEW_PERMISSIONS=["*"])
    def test_member_zones_panel_links_the_members_beyond_the_first_five(self):
        """The Member Zones panel shows five members and links the zone list for the rest."""
        for index in range(5):
            create_zone(f"more-{index}.example", catalog_zone=self.catalog_zone)
        content = self._detail(self.catalog_zone)
        self.assertIn("View 1 more Member Zones", content)
        self.assertIn(
            f"{reverse('plugins:nautobot_dns_models:dnszone_list')}?catalog_zone={self.catalog_zone.pk}", content
        )

    @override_settings(EXEMPT_VIEW_PERMISSIONS=["*"])
    def test_member_zones_panel_has_no_more_link_with_five_members_or_fewer(self):
        """The Member Zones panel has no link to further members when it shows them all."""
        self.assertNotIn("more Member Zones", self._detail(self.catalog_zone))

    @override_settings(EXEMPT_VIEW_PERMISSIONS=["*"])
    def test_primary_zone_has_no_member_zones_panel(self):
        """An ordinary zone renders no Member Zones panel, having no members to publish."""
        self.assertNotIn("MEMBER ZONES", self._panel_headings(self.member_zone))

    @override_settings(EXEMPT_VIEW_PERMISSIONS=["*"])
    def test_member_zone_names_the_catalog_it_belongs_to(self):
        """A member zone carries a Catalog Zone row linking the catalog holding it."""
        content = self._detail(self.member_zone)
        self.assertInHTML("<td>Catalog Zone</td>", content, 1)
        self.assertIn(self.catalog_zone.get_absolute_url(), content)

    @override_settings(EXEMPT_VIEW_PERMISSIONS=["*"])
    def test_member_zone_has_no_member_label_row(self):
        """A member zone's fields panel leaves out its member label."""
        content = self._detail(self.member_zone)
        self.assertInHTML("<td>Member Label</td>", content, 0)
        self.assertNotIn(self.member_zone.member_label, content)

    @override_settings(EXEMPT_VIEW_PERMISSIONS=["*"])
    def test_catalog_zone_omits_the_membership_fields(self):
        """A catalog zone carries no Catalog Zone or Member Label row."""
        content = self._detail(self.catalog_zone)
        self.assertInHTML("<td>Catalog Zone</td>", content, 0)
        self.assertInHTML("<td>Member Label</td>", content, 0)


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


class DNSZoneEditViewTest(TestCase):
    """Tests for the catalog field of the zone add and edit pages, for a user who may change only some catalogs."""

    @classmethod
    def setUpTestData(cls):
        cls.catalog_zone = create_zone("edit-catalog.example", type=DNSZoneTypeChoices.TYPE_CATALOG)
        cls.other_catalog = create_zone("edit-other-catalog.example", type=DNSZoneTypeChoices.TYPE_CATALOG)
        cls.member_zone = create_zone("edit-member.example", catalog_zone=cls.other_catalog)

    def setUp(self):
        """Grant the view permission the form's view field needs to accept the zone's view."""
        super().setUp()
        self.add_permissions("nautobot_dns_models.view_dnsview")

    def _zone_data(self, zone, **overrides):
        """Return an edit form payload for `zone` as stored, with any supplied overrides applied."""
        data = {
            "name": zone.name,
            "type": zone.type,
            "dns_view": str(zone.dns_view_id),
            "ttl": zone.ttl,
            "filename": zone.filename,
            "soa_mname": zone.soa_mname,
            "soa_rname": zone.soa_rname,
            "soa_refresh": zone.soa_refresh,
            "soa_retry": zone.soa_retry,
            "soa_expire": zone.soa_expire,
            "soa_serial": zone.soa_serial,
            "soa_minimum": zone.soa_minimum,
            "catalog_zone": str(zone.catalog_zone_id or ""),
            "enabled": "on",
        }
        data.update(overrides)
        return data

    def test_the_add_page_refuses_a_catalog_the_user_cannot_change(self):
        """Adding a zone to a catalog the user may not change is refused on the catalog field."""
        permit_zone_change(self.user, self.catalog_zone)
        self.add_permissions("nautobot_dns_models.add_dnszone")
        new_zone = DNSZone(
            name="edit-new.example",
            filename="edit-new.example.zone",
            soa_mname="ns1.edit-new.example.",
            soa_rname="admin@edit-new.example",
        )
        response = self.client.post(
            reverse("plugins:nautobot_dns_models:dnszone_add"),
            self._zone_data(new_zone, catalog_zone=str(self.other_catalog.pk)),
        )

        self.assertHttpStatus(response, 200)
        self.assertFalse(DNSZone.objects.filter(name=new_zone.name).exists())
        errors = response.context["form"].errors
        self.assertEqual(list(errors), ["catalog_zone"])
        # The field's own refusal, rather than the model's, which would follow if the field offered the catalog.
        self.assertIn("Select a valid choice", errors["catalog_zone"][0])

    def test_a_member_of_a_catalog_the_user_cannot_change_keeps_it_through_an_edit(self):
        """The edit page disables the catalog field, so other edits save and the zone keeps its catalog."""
        permit_zone_change(self.user, self.member_zone)
        url = reverse("plugins:nautobot_dns_models:dnszone_edit", kwargs={"pk": self.member_zone.pk})

        response = self.client.get(url)
        self.assertHttpStatus(response, 200)
        self.assertIn(
            "Changing this zone's catalog requires permission to change its catalog zone.",
            extract_page_body(response.content.decode(response.charset)),
        )

        response = self.client.post(url, self._zone_data(self.member_zone, description="Edited", catalog_zone=""))
        self.assertRedirects(response, self.member_zone.get_absolute_url(), fetch_redirect_response=False)
        self.member_zone.refresh_from_db()
        self.assertEqual(self.member_zone.description, "Edited")
        self.assertEqual(self.member_zone.catalog_zone, self.other_catalog)


# Job logs otherwise go through their own connection, which cannot be used inside a `TestCase` transaction.
@patch("nautobot.extras.models.jobs.JOB_LOGS", None)
class DNSZoneBulkEditViewTest(TestCase):
    """Tests for the zone bulk edit page and the job it queues.

    A catalog zone refuses `auto_create_ptr` and a catalog of its own, and the bulk edit job saves each
    object in turn, so the page withdraws both controls once a catalog zone is among the selection.
    The job builds the form without the selection, so the view check in the form's `clean()` does not
    run there; the model refuses each zone instead, and the job's transaction takes the batch back.
    """

    NULLIFY_CATALOG_ZONE = 'name="_nullify" type="checkbox" value="catalog_zone"'
    WITHDRAWN = "Catalog zones cannot enable this, and the selection includes one."

    @classmethod
    def setUpTestData(cls):
        cls.catalog_zone = create_zone("bulk-catalog.example", type=DNSZoneTypeChoices.TYPE_CATALOG)
        cls.zones = [create_zone(f"bulk-member-{index}.example") for index in range(3)]
        cls.other_view = DNSView.objects.create(name="Bulk Other View")
        cls.other_view_zone = create_zone("bulk-other-view.example", dns_view=cls.other_view)
        cls.zone_content_type = ContentType.objects.get_for_model(DNSZone)

    def setUp(self):
        """Grant the permissions a bulk edit needs before its selection is judged."""
        super().setUp()
        self.add_permissions("nautobot_dns_models.view_dnszone", "nautobot_dns_models.change_dnszone")

    def _bulk_edit_form(self, pk_list=None, edit_all=False, query="", **fields):
        """Return the bulk edit page rendered for a selection, named by pk or claimed wholesale."""
        data = {"pk": [str(pk) for pk in pk_list or []], **fields}
        if edit_all:
            data["_all"] = "on"

        url = reverse("plugins:nautobot_dns_models:dnszone_bulk_edit")
        response = self.client.post(f"{url}{query}", data)
        self.assertHttpStatus(response, 200)
        return extract_page_body(response.content.decode(response.charset))

    def _run(self, zones, username="test-user", **form_data):
        """Run the bulk edit job against `zones` as `username`, returning its result."""
        pk_list = [str(zone.pk) for zone in zones]
        return create_job_result_and_run_job(
            "nautobot.core.jobs.bulk_actions",
            "BulkEditObjects",
            content_type=self.zone_content_type.pk,
            edit_all=False,
            filter_query_params={},
            pk_list=pk_list,
            form_data={"pk": pk_list, **form_data},
            username=username,
        )

    def test_a_selection_of_primary_zones_offers_the_control(self):
        """A selection of primary zones renders the `auto_create_ptr` control."""
        content = self._bulk_edit_form(pk_list=[zone.pk for zone in self.zones])
        self.assertIn('name="auto_create_ptr"', content)
        self.assertNotIn(self.WITHDRAWN, content)

    def test_the_catalog_field_asks_for_catalogs_the_user_can_change(self):
        """The catalog field asks for catalog zones the user may change."""
        content = self._bulk_edit_form(pk_list=[zone.pk for zone in self.zones])
        self.assertIn('data-query-param-can_change="[&quot;True&quot;]"', content)

    def test_a_selection_holding_a_catalog_zone_withdraws_the_control(self):
        """A catalog zone in the selection withdraws the `auto_create_ptr` control."""
        content = self._bulk_edit_form(pk_list=[self.zones[0].pk, self.catalog_zone.pk])
        self.assertIn(self.WITHDRAWN, content)

    def test_select_all_withdraws_the_control_when_it_includes_a_catalog_zone(self):
        """'Select All' withdraws `auto_create_ptr` when it includes a catalog zone.

        Unfiltered, it resolves to every zone, the catalog zone among them.
        """
        self.assertIn(self.WITHDRAWN, self._bulk_edit_form(edit_all=True))

    def test_select_all_keeps_the_control_when_filtered_to_primary_zones(self):
        """'Select All' keeps `auto_create_ptr` when filtered to primary zones."""
        content = self._bulk_edit_form(edit_all=True, query=f"?type={DNSZoneTypeChoices.TYPE_PRIMARY}")
        self.assertIn('name="auto_create_ptr"', content)
        self.assertNotIn(self.WITHDRAWN, content)

    def test_the_page_refuses_a_catalog_some_of_the_selection_cannot_be_added_to(self):
        """Bulk edit refuses a catalog outside the selection's new view before queueing a job."""
        self.add_permissions("nautobot_dns_models.view_dnsview")
        content = self._bulk_edit_form(
            pk_list=[zone.pk for zone in self.zones],
            _apply="",
            catalog_zone=str(self.catalog_zone.pk),
            dns_view=str(self.other_view.pk),
        )
        self.assertIn("The selected zones must be in the same view as the catalog zone.", content)

    def test_a_selection_of_member_candidates_offers_set_null_for_the_catalog(self):
        """A selection of primary zones offers set-null for the catalog."""
        content = self._bulk_edit_form(pk_list=[zone.pk for zone in self.zones])
        self.assertIn(self.NULLIFY_CATALOG_ZONE, content)

    def test_a_selection_holding_a_catalog_zone_offers_no_set_null_for_the_catalog(self):
        """A selection that includes a catalog zone offers no set-null for the catalog.

        A catalog zone cannot be a member of a catalog, so the catalog field is shown disabled and
        its set-null option is removed.
        """
        content = self._bulk_edit_form(pk_list=[self.zones[0].pk, self.catalog_zone.pk])
        self.assertIn('name="catalog_zone"', content)
        self.assertNotIn(self.NULLIFY_CATALOG_ZONE, content)

    def test_adding_gives_each_zone_its_own_label_and_ptr_record(self):
        """Adding zones to a catalog in bulk gives each its own label and PTR record."""
        job_result = self._run(self.zones, catalog_zone=str(self.catalog_zone.pk))

        self.assertEqual(job_result.status, JobResultStatusChoices.STATUS_SUCCESS)
        labels = set()
        for zone in self.zones:
            zone.refresh_from_db()
            self.assertEqual(zone.catalog_zone, self.catalog_zone)
            labels.add(zone.member_label)
            self.assertTrue(PTRRecord.objects.filter(zone=self.catalog_zone, name=zone.ptr_record_name).exists())

        self.assertEqual(len(labels), len(self.zones))

    def test_nulling_the_catalog_withdraws_each_zone(self):
        """Nulling the catalog in bulk withdraws each zone's PTR record and logs each delete."""
        for zone in self.zones:
            zone.catalog_zone = self.catalog_zone
            zone.validated_save()

        ptr_record_pks = set(
            PTRRecord.objects.filter(zone=self.catalog_zone, name__endswith=".zones").values_list("pk", flat=True)
        )

        job_result = self._run(self.zones, _nullify=["catalog_zone"])

        self.assertEqual(job_result.status, JobResultStatusChoices.STATUS_SUCCESS)
        for zone in self.zones:
            zone.refresh_from_db()
            self.assertIsNone(zone.catalog_zone)
            self.assertEqual(zone.member_label, "")

        self.assertFalse(PTRRecord.objects.filter(zone=self.catalog_zone, name__endswith=".zones").exists())
        # Each withdrawn record is logged against its own id, though the job logs them only once it ends.
        logged_pks = ObjectChange.objects.filter(
            changed_object_type=ContentType.objects.get_for_model(PTRRecord),
            action=ObjectChangeActionChoices.ACTION_DELETE,
        ).values_list("changed_object_id", flat=True)

        self.assertEqual(set(logged_pks), ptr_record_pks)

    def test_one_zone_in_a_different_view_fails_the_whole_batch(self):
        """One zone in a different view fails the bulk add, and no zone is added."""
        job_result = self._run([*self.zones, self.other_view_zone], catalog_zone=str(self.catalog_zone.pk))

        self.assertEqual(job_result.status, JobResultStatusChoices.STATUS_FAILURE)
        self.assertFalse(DNSZone.objects.filter(catalog_zone=self.catalog_zone).exists())
        self.assertFalse(PTRRecord.objects.filter(zone=self.catalog_zone, name__endswith=".zones").exists())

    def test_adding_needs_change_permission_on_the_catalog(self):
        """A bulk add without change permission on the catalog is refused, and no zone is added."""
        user = User.objects.create_user(username="bulk-catalog-user")
        permit_zone_change(user, *self.zones)

        job_result = self._run(self.zones, username=user.username, catalog_zone=str(self.catalog_zone.pk))

        self.assertEqual(job_result.status, JobResultStatusChoices.STATUS_FAILURE)
        self.assertFalse(DNSZone.objects.filter(catalog_zone=self.catalog_zone).exists())

    def test_adding_succeeds_with_change_permission_on_the_catalog(self):
        """A bulk add succeeds with change permission on the zones and the catalog."""
        user = User.objects.create_user(username="bulk-catalog-user")
        permit_zone_change(user, *self.zones, self.catalog_zone)

        job_result = self._run(self.zones, username=user.username, catalog_zone=str(self.catalog_zone.pk))

        self.assertEqual(job_result.status, JobResultStatusChoices.STATUS_SUCCESS)
        self.assertEqual(DNSZone.objects.filter(catalog_zone=self.catalog_zone).count(), len(self.zones))


# Job logs otherwise go through their own connection, which cannot be used inside a `TestCase` transaction.
@patch("nautobot.extras.models.jobs.JOB_LOGS", None)
class DNSZoneBulkDeleteViewTest(TestCase):
    """Tests for deleting catalog zones and their members through the bulk delete job."""

    @classmethod
    def setUpTestData(cls):
        cls.catalog_zone = create_zone("delete-catalog.example", type=DNSZoneTypeChoices.TYPE_CATALOG)
        cls.zones = [create_zone(f"delete-member-{index}.example", catalog_zone=cls.catalog_zone) for index in range(2)]

    def _run(self, zones, username="test-user"):
        """Run the bulk delete job against `zones` as `username`, returning its result."""
        return create_job_result_and_run_job(
            "nautobot.core.jobs.bulk_actions",
            "BulkDeleteObjects",
            content_type=ContentType.objects.get_for_model(DNSZone).pk,
            delete_all=False,
            filter_query_params={},
            pk_list=[str(zone.pk) for zone in zones],
            username=username,
        )

    def _user_permitted_to_delete(self, *catalog_zones):
        """Return a user who may view and delete every zone, and change only `catalog_zones`."""
        user = User.objects.create_user(username="bulk-delete-user")
        permit_zone_change(user, *catalog_zones)
        delete_permission = ObjectPermission.objects.create(name="delete zones", actions=["delete"])
        delete_permission.object_types.set([ContentType.objects.get_for_model(DNSZone)])
        delete_permission.users.add(user)
        return user

    def test_deleting_members_withdraws_and_logs_their_ptr_records(self):
        """Bulk deleting members withdraws their PTR records and logs each delete."""
        ptr_record_pks = set(
            PTRRecord.objects.filter(zone=self.catalog_zone, name__endswith=".zones").values_list("pk", flat=True)
        )
        self.assertEqual(len(ptr_record_pks), len(self.zones))

        job_result = self._run(self.zones)

        self.assertEqual(job_result.status, JobResultStatusChoices.STATUS_SUCCESS)
        self.assertFalse(PTRRecord.objects.filter(pk__in=ptr_record_pks).exists())
        deletes = ObjectChange.objects.filter(action=ObjectChangeActionChoices.ACTION_DELETE)
        logged_zone_pks = deletes.filter(changed_object_type=ContentType.objects.get_for_model(DNSZone)).values_list(
            "changed_object_id", flat=True
        )
        self.assertEqual(set(logged_zone_pks), {zone.pk for zone in self.zones})
        logged_ptr_pks = deletes.filter(changed_object_type=ContentType.objects.get_for_model(PTRRecord)).values_list(
            "changed_object_id", flat=True
        )
        self.assertEqual(set(logged_ptr_pks), ptr_record_pks)

    def test_deleting_members_needs_change_permission_on_the_catalog(self):
        """A bulk delete of members without change permission on their catalog is refused.

        No member is deleted and no PTR record is withdrawn, so the catalog still lists every member.
        """
        user = self._user_permitted_to_delete()
        ptr_record_pks = set(PTRRecord.objects.filter(zone=self.catalog_zone).values_list("pk", flat=True))

        job_result = self._run(self.zones, username=user.username)

        self.assertEqual(job_result.status, JobResultStatusChoices.STATUS_FAILURE)
        self.assertEqual(DNSZone.objects.filter(pk__in=[zone.pk for zone in self.zones]).count(), len(self.zones))
        self.assertEqual(
            set(PTRRecord.objects.filter(zone=self.catalog_zone).values_list("pk", flat=True)), ptr_record_pks
        )

    def test_deleting_members_succeeds_with_change_permission_on_the_catalog(self):
        """A bulk delete of members succeeds with change permission on their catalog."""
        user = self._user_permitted_to_delete(self.catalog_zone)

        job_result = self._run(self.zones, username=user.username)

        self.assertEqual(job_result.status, JobResultStatusChoices.STATUS_SUCCESS)
        self.assertFalse(DNSZone.objects.filter(pk__in=[zone.pk for zone in self.zones]).exists())

    def test_an_empty_catalog_zone_is_deleted_with_its_records(self):
        """Bulk deleting an empty catalog zone deletes its NS and TXT records with it."""
        empty_catalog_zone = create_zone("empty-catalog.example", type=DNSZoneTypeChoices.TYPE_CATALOG)

        job_result = self._run([empty_catalog_zone])

        self.assertEqual(job_result.status, JobResultStatusChoices.STATUS_SUCCESS)
        self.assertFalse(DNSZone.objects.filter(pk=empty_catalog_zone.pk).exists())
        for record_model in (NSRecord, TXTRecord):
            self.assertFalse(record_model.objects.filter(zone_id=empty_catalog_zone.pk).exists())

    def test_a_catalog_with_members_is_refused(self):
        """Bulk deleting a catalog zone that has members is refused."""
        job_result = self._run([self.catalog_zone])

        self.assertEqual(job_result.status, JobResultStatusChoices.STATUS_FAILURE)
        self.assertTrue(DNSZone.objects.filter(pk=self.catalog_zone.pk).exists())

    def test_a_refused_delete_keeps_every_record(self):
        """A refused bulk delete leaves the member and the catalog's records in place.

        The selection is one member and its catalog. The catalog still has members, so the delete
        is refused, and the member, which could have been deleted on its own, keeps its PTR record.
        """
        records = {
            record_model: set(record_model.objects.filter(zone=self.catalog_zone).values_list("pk", flat=True))
            for record_model in (NSRecord, TXTRecord, PTRRecord)
        }

        job_result = self._run([self.zones[0], self.catalog_zone])

        self.assertEqual(job_result.status, JobResultStatusChoices.STATUS_FAILURE)
        self.assertTrue(DNSZone.objects.filter(pk=self.zones[0].pk).exists())
        for record_model, pks in records.items():
            self.assertEqual(set(record_model.objects.filter(zone=self.catalog_zone).values_list("pk", flat=True)), pks)

    def test_a_catalog_selected_with_all_its_members_is_refused(self):
        """A catalog deleted together with all its members is still refused.

        Django's Collector refuses a protected reference even from a zone deleted in the same batch.
        """
        job_result = self._run([self.catalog_zone, *self.zones])

        self.assertEqual(job_result.status, JobResultStatusChoices.STATUS_FAILURE)
        self.assertEqual(
            DNSZone.objects.filter(pk__in=[self.catalog_zone.pk, *(zone.pk for zone in self.zones)]).count(), 3
        )
        self.assertEqual(PTRRecord.objects.filter(zone=self.catalog_zone, name__endswith=".zones").count(), 2)


class DNSZoneCatalogMembershipViewTest(TestCase):
    """Tests for adding zones to a catalog zone and removing them through the UI.

    Covers the `add_member`, `add_to_catalog` and `remove_from_catalog` actions, and the links to them on the
    catalog zone's Member Zones panel and in the zone list.
    """

    @classmethod
    def setUpTestData(cls):
        cls.catalog_zone = create_zone("membership-catalog.example", type=DNSZoneTypeChoices.TYPE_CATALOG)
        cls.other_catalog = create_zone("membership-other-catalog.example", type=DNSZoneTypeChoices.TYPE_CATALOG)
        cls.other_view = DNSView.objects.create(name="Membership Other View")
        cls.other_view_catalog = create_zone(
            "membership-other-view-catalog.example", type=DNSZoneTypeChoices.TYPE_CATALOG, dns_view=cls.other_view
        )
        cls.other_view_zone = create_zone("membership-other-view.example", dns_view=cls.other_view)
        cls.zone = create_zone("membership-zone.example")
        cls.member_zone = create_zone("membership-member.example", catalog_zone=cls.catalog_zone)
        cls.enrolled_zone = create_zone("membership-enrolled.example", catalog_zone=cls.other_catalog)

    def _detail(self, zone):
        """Return the rendered body of `zone`'s detail page."""
        response = self.client.get(zone.get_absolute_url())
        self.assertHttpStatus(response, 200)
        return extract_page_body(response.content.decode(response.charset))

    def _list(self):
        """Return the rendered rows of the zone list, which arrive on the HTMX follow-up request."""
        response = self.client.get(reverse("plugins:nautobot_dns_models:dnszone_list"), headers={"HX-Request": "true"})
        self.assertHttpStatus(response, 200)
        return extract_page_body(response.content.decode(response.charset))

    def _post_add_member_refused(self, zone):
        """Post `zone` to the add-member page, assert it was not added, and return the re-rendered page."""
        url = reverse("plugins:nautobot_dns_models:dnszone_add_member", kwargs={"pk": self.catalog_zone.pk})
        response = self.client.post(url, {"zone": str(zone.pk), "_save": ""})
        self.assertHttpStatus(response, 200)
        self.assertFalse(DNSZone.objects.filter(pk=zone.pk, catalog_zone=self.catalog_zone).exists())
        return extract_page_body(response.content.decode(response.charset))

    def _post_add_to_catalog_refused(self, catalog_zone):
        """Post `catalog_zone` to the add-to-catalog page, assert the zone was not added, and return the re-rendered page."""
        url = reverse("plugins:nautobot_dns_models:dnszone_add_to_catalog", kwargs={"pk": self.zone.pk})
        response = self.client.post(url, {"catalog_zone": str(catalog_zone.pk), "_save": ""})
        self.assertHttpStatus(response, 200)
        self.zone.refresh_from_db()
        self.assertIsNone(self.zone.catalog_zone)
        return extract_page_body(response.content.decode(response.charset))

    def test_the_panel_offers_add_with_change_permission(self):
        """A user who may change every zone is offered Add Member Zone on the catalog."""
        self.add_permissions("nautobot_dns_models.view_dnszone", "nautobot_dns_models.change_dnszone")
        url = reverse("plugins:nautobot_dns_models:dnszone_add_member", kwargs={"pk": self.catalog_zone.pk})
        content = self._detail(self.catalog_zone)
        self.assertIn(url, content)
        self.assertIn("Add Member Zone", content)

    def test_the_panel_offers_no_add_without_change_permission(self):
        """A user who may only view zones is not offered Add Member Zone."""
        self.add_permissions("nautobot_dns_models.view_dnszone")
        url = reverse("plugins:nautobot_dns_models:dnszone_add_member", kwargs={"pk": self.catalog_zone.pk})
        self.assertNotIn(url, self._detail(self.catalog_zone))

    def test_the_panel_offers_no_add_when_the_user_cannot_change_the_catalog(self):
        """Add Member Zone is not offered without change permission on the catalog."""
        permit_zone_change(self.user, self.zone)
        url = reverse("plugins:nautobot_dns_models:dnszone_add_member", kwargs={"pk": self.catalog_zone.pk})
        self.assertNotIn(url, self._detail(self.catalog_zone))

    def test_the_panel_offers_no_add_when_the_user_can_change_no_candidate(self):
        """Add Member Zone is not offered when the user can change no zone that could be added."""
        permit_zone_change(self.user, self.catalog_zone, self.enrolled_zone, self.other_view_zone)
        url = reverse("plugins:nautobot_dns_models:dnszone_add_member", kwargs={"pk": self.catalog_zone.pk})
        self.assertNotIn(url, self._detail(self.catalog_zone))

    def test_the_panel_offers_add_when_the_user_can_change_the_catalog_and_a_candidate(self):
        """Add Member Zone is offered with change permission on the catalog and at least one candidate."""
        permit_zone_change(self.user, self.catalog_zone, self.zone)
        url = reverse("plugins:nautobot_dns_models:dnszone_add_member", kwargs={"pk": self.catalog_zone.pk})
        self.assertIn(url, self._detail(self.catalog_zone))

    def test_the_panel_offers_remove_with_change_permission(self):
        """A user who may change every zone sees Remove from Catalog on each member's row."""
        self.add_permissions("nautobot_dns_models.view_dnszone", "nautobot_dns_models.change_dnszone")
        url = reverse("plugins:nautobot_dns_models:dnszone_remove_from_catalog", kwargs={"pk": self.member_zone.pk})
        content = self._detail(self.catalog_zone)
        self.assertIn(url, content)
        self.assertIn("Remove from Catalog", content)

    def test_the_panel_offers_no_remove_without_change_permission(self):
        """A user who may only view zones is not offered Remove from Catalog."""
        self.add_permissions("nautobot_dns_models.view_dnszone")
        url = reverse("plugins:nautobot_dns_models:dnszone_remove_from_catalog", kwargs={"pk": self.member_zone.pk})
        self.assertNotIn(url, self._detail(self.catalog_zone))

    def test_the_panel_offers_no_remove_with_permission_on_only_one_zone(self):
        """Remove from Catalog is not offered with permission on only the member or the catalog."""
        url = reverse("plugins:nautobot_dns_models:dnszone_remove_from_catalog", kwargs={"pk": self.member_zone.pk})
        for zone in (self.member_zone, self.catalog_zone):
            with self.subTest(zone=zone.name):
                ObjectPermission.objects.filter(users=self.user).delete()
                permit_zone_change(self.user, zone)
                self.assertNotIn(url, self._detail(self.catalog_zone))

    def test_the_list_offers_add_to_zones_in_no_catalog_and_remove_to_members(self):
        """Each list row offers the one catalog action that applies and catalog zones offer none."""
        self.add_permissions("nautobot_dns_models.view_dnszone", "nautobot_dns_models.change_dnszone")
        body = self._list()
        for zone, offers_add, offers_remove in (
            (self.zone, True, False),
            (self.member_zone, False, True),
            (self.catalog_zone, False, False),
        ):
            add_url = reverse("plugins:nautobot_dns_models:dnszone_add_to_catalog", kwargs={"pk": zone.pk})
            remove_url = reverse("plugins:nautobot_dns_models:dnszone_remove_from_catalog", kwargs={"pk": zone.pk})
            with self.subTest(zone=zone.name):
                self.assertEqual(add_url in body, offers_add)
                self.assertEqual(remove_url in body, offers_remove)

    def test_the_list_offers_neither_without_change_permission(self):
        """A user who may only view zones is offered no catalog action in the list."""
        self.add_permissions("nautobot_dns_models.view_dnszone")
        body = self._list()
        self.assertNotIn("Add to Catalog", body)
        self.assertNotIn("Remove from Catalog", body)

    def test_the_list_offers_add_only_on_zones_the_user_can_change(self):
        """Add to Catalog appears only on the rows of zones the user may change."""
        permit_zone_change(self.user, self.catalog_zone, self.zone)
        url = reverse("plugins:nautobot_dns_models:dnszone_add_to_catalog", kwargs={"pk": self.zone.pk})
        body = self._list()
        self.assertIn(url, body)
        self.assertEqual(body.count("Add to Catalog"), 1)

    def test_the_list_offers_no_add_without_a_catalog_the_user_can_change_in_the_view(self):
        """Add to Catalog is not offered when the user can change no catalog in the zone's view."""
        permit_zone_change(self.user, self.zone, self.other_view_catalog)
        url = reverse("plugins:nautobot_dns_models:dnszone_add_to_catalog", kwargs={"pk": self.zone.pk})
        self.assertNotIn(url, self._list())

    def test_the_list_offers_remove_only_with_permission_on_the_member_and_its_catalog(self):
        """The list offers Remove from Catalog only with permission on the member and its catalog."""
        url = reverse("plugins:nautobot_dns_models:dnszone_remove_from_catalog", kwargs={"pk": self.member_zone.pk})
        cases = (
            ((self.member_zone,), False),
            ((self.catalog_zone,), False),
            ((self.member_zone, self.catalog_zone), True),
        )
        for zones, offered in cases:
            with self.subTest(zones=[zone.name for zone in zones]):
                ObjectPermission.objects.filter(users=self.user).delete()
                permit_zone_change(self.user, *zones)
                self.assertEqual(url in self._list(), offered)

    def test_the_add_member_page_offers_a_zone_field(self):
        """The add-member page offers only zones in the catalog's view that are not in a catalog."""
        self.add_permissions("nautobot_dns_models.view_dnszone", "nautobot_dns_models.change_dnszone")
        url = reverse("plugins:nautobot_dns_models:dnszone_add_member", kwargs={"pk": self.catalog_zone.pk})
        response = self.client.get(url)
        self.assertHttpStatus(response, 200)
        body = extract_page_body(response.content.decode(response.charset))
        self.assertIn('name="zone"', body)
        self.assertIn(f'data-query-param-dns_view="[&quot;{self.catalog_zone.dns_view_id}&quot;]"', body)
        self.assertIn('data-query-param-is_catalog_member="[&quot;False&quot;]"', body)
        self.assertIn('data-query-param-can_change="[&quot;True&quot;]"', body)

    def test_adding_a_member_publishes_it_and_returns_to_the_catalog(self):
        """Adding a member from the catalog's page publishes it and returns to the catalog."""
        self.add_permissions("nautobot_dns_models.view_dnszone", "nautobot_dns_models.change_dnszone")
        url = reverse("plugins:nautobot_dns_models:dnszone_add_member", kwargs={"pk": self.catalog_zone.pk})
        response = self.client.post(url, {"zone": str(self.zone.pk), "_save": ""})

        self.assertRedirects(response, self.catalog_zone.get_absolute_url(), fetch_redirect_response=False)
        self.zone.refresh_from_db()
        self.assertEqual(self.zone.catalog_zone, self.catalog_zone)
        self.assertTrue(PTRRecord.objects.filter(zone=self.catalog_zone, name=self.zone.ptr_record_name).exists())

    def test_add_another_returns_to_the_add_member_page(self):
        """The "Save and Add Another" button brings the user back to the add-member page for the next zone."""
        self.add_permissions("nautobot_dns_models.view_dnszone", "nautobot_dns_models.change_dnszone")
        url = reverse("plugins:nautobot_dns_models:dnszone_add_member", kwargs={"pk": self.catalog_zone.pk})
        response = self.client.post(url, {"zone": str(self.zone.pk), "_addanother": ""})
        self.assertRedirects(response, url, fetch_redirect_response=False)

    def test_the_add_member_page_cannot_add_a_zone_in_a_different_view(self):
        """The add-member page refuses a zone in a different view, on the zone field."""
        self.add_permissions("nautobot_dns_models.view_dnszone", "nautobot_dns_models.change_dnszone")
        body = self._post_add_member_refused(self.other_view_zone)
        self.assertIn("The catalog zone must be in the same view as this zone.", body)

    def test_the_add_member_page_refuses_a_zone_already_in_a_catalog(self):
        """The add-member page refuses a zone already in another catalog and leaves it there."""
        self.add_permissions("nautobot_dns_models.view_dnszone", "nautobot_dns_models.change_dnszone")
        body = self._post_add_member_refused(self.enrolled_zone)
        self.assertIn(f"Zone {self.enrolled_zone} is already a member of catalog zone {self.other_catalog}.", body)
        self.enrolled_zone.refresh_from_db()
        self.assertEqual(self.enrolled_zone.catalog_zone, self.other_catalog)

    def test_the_add_member_page_refuses_a_zone_the_user_cannot_change(self):
        """The add-member page refuses a zone the user cannot change."""
        permit_zone_change(self.user, self.catalog_zone)
        self._post_add_member_refused(self.zone)

    def test_a_catalog_the_user_cannot_change_has_no_add_member_page(self):
        """A catalog the user cannot change has no add-member page."""
        permit_zone_change(self.user, self.zone)
        url = reverse("plugins:nautobot_dns_models:dnszone_add_member", kwargs={"pk": self.catalog_zone.pk})
        self.assertHttpStatus(self.client.get(url), 404)

    def test_a_primary_zone_has_no_add_member_page(self):
        """A primary zone has no add-member page."""
        self.add_permissions("nautobot_dns_models.view_dnszone", "nautobot_dns_models.change_dnszone")
        url = reverse("plugins:nautobot_dns_models:dnszone_add_member", kwargs={"pk": self.zone.pk})
        self.assertHttpStatus(self.client.get(url), 404)

    def test_the_add_to_catalog_page_offers_a_catalog_field(self):
        """The add-to-catalog page's catalog field lists only catalog zones in the zone's view.

        The page has no zone field, as the zone comes from the URL, and no "Save and Add Another" button,
        as a zone is in only one catalog.
        """
        self.add_permissions("nautobot_dns_models.view_dnszone", "nautobot_dns_models.change_dnszone")
        url = reverse("plugins:nautobot_dns_models:dnszone_add_to_catalog", kwargs={"pk": self.zone.pk})
        response = self.client.get(url)
        self.assertHttpStatus(response, 200)
        body = extract_page_body(response.content.decode(response.charset))
        self.assertIn('name="catalog_zone"', body)
        self.assertNotIn('name="zone"', body)
        self.assertNotIn('name="_addanother"', body)
        self.assertIn(f'data-query-param-dns_view="[&quot;{self.zone.dns_view_id}&quot;]"', body)
        self.assertIn(f'data-query-param-type="[&quot;{DNSZoneTypeChoices.TYPE_CATALOG}&quot;]"', body)
        self.assertIn('data-query-param-can_change="[&quot;True&quot;]"', body)

    def test_adding_to_a_catalog_publishes_the_zone_and_returns_to_it(self):
        """Adding a zone to a catalog from the zone's page publishes it and returns to the zone."""
        self.add_permissions("nautobot_dns_models.view_dnszone", "nautobot_dns_models.change_dnszone")
        url = reverse("plugins:nautobot_dns_models:dnszone_add_to_catalog", kwargs={"pk": self.zone.pk})
        response = self.client.post(url, {"catalog_zone": str(self.catalog_zone.pk), "_save": ""})

        self.assertRedirects(response, self.zone.get_absolute_url(), fetch_redirect_response=False)
        self.zone.refresh_from_db()
        self.assertEqual(self.zone.catalog_zone, self.catalog_zone)
        self.assertTrue(PTRRecord.objects.filter(zone=self.catalog_zone, name=self.zone.ptr_record_name).exists())

    def test_the_add_to_catalog_page_cannot_add_to_a_catalog_zone_in_a_different_view(self):
        """The add-to-catalog page refuses a catalog zone in a different view, on the catalog field."""
        self.add_permissions("nautobot_dns_models.view_dnszone", "nautobot_dns_models.change_dnszone")
        body = self._post_add_to_catalog_refused(self.other_view_catalog)
        self.assertIn("The catalog zone must be in the same view as this zone.", body)

    def test_the_add_to_catalog_page_refuses_a_catalog_the_user_cannot_change(self):
        """The add-to-catalog page refuses a catalog the user cannot change."""
        permit_zone_change(self.user, self.zone)
        self._post_add_to_catalog_refused(self.catalog_zone)

    def test_a_zone_the_user_cannot_change_has_no_add_to_catalog_page(self):
        """A zone the user cannot change has no add-to-catalog page."""
        permit_zone_change(self.user, self.catalog_zone)
        url = reverse("plugins:nautobot_dns_models:dnszone_add_to_catalog", kwargs={"pk": self.zone.pk})
        self.assertHttpStatus(self.client.get(url), 404)

    def test_a_member_or_catalog_zone_has_no_add_to_catalog_page(self):
        """A member zone or a catalog zone has no add-to-catalog page."""
        self.add_permissions("nautobot_dns_models.view_dnszone", "nautobot_dns_models.change_dnszone")
        for zone in (self.member_zone, self.catalog_zone):
            with self.subTest(zone=zone.name):
                url = reverse("plugins:nautobot_dns_models:dnszone_add_to_catalog", kwargs={"pk": zone.pk})
                self.assertHttpStatus(self.client.get(url), 404)

    def test_the_remove_page_asks_for_confirmation(self):
        """Opening the remove page names the member and its catalog, and removes nothing."""
        self.add_permissions("nautobot_dns_models.view_dnszone", "nautobot_dns_models.change_dnszone")
        url = reverse("plugins:nautobot_dns_models:dnszone_remove_from_catalog", kwargs={"pk": self.member_zone.pk})
        response = self.client.get(url)
        self.assertHttpStatus(response, 200)
        body = extract_page_body(response.content.decode(response.charset))
        self.assertIn(f"remove <strong>{self.member_zone}</strong> from catalog zone {self.catalog_zone}?", body)
        self.member_zone.refresh_from_db()
        self.assertEqual(self.member_zone.catalog_zone, self.catalog_zone)

    def test_confirming_removal_withdraws_the_member_and_returns_to_the_catalog(self):
        """Confirming removal withdraws the member's PTR record and returns to the catalog."""
        self.add_permissions("nautobot_dns_models.view_dnszone", "nautobot_dns_models.change_dnszone")
        ptr_record_name = self.member_zone.ptr_record_name
        url = reverse("plugins:nautobot_dns_models:dnszone_remove_from_catalog", kwargs={"pk": self.member_zone.pk})
        response = self.client.post(url, {"confirm": "true"})

        self.assertRedirects(response, self.catalog_zone.get_absolute_url(), fetch_redirect_response=False)
        self.member_zone.refresh_from_db()
        self.assertIsNone(self.member_zone.catalog_zone)
        self.assertFalse(PTRRecord.objects.filter(zone=self.catalog_zone, name=ptr_record_name).exists())

    def test_an_unconfirmed_removal_removes_nothing(self):
        """An unconfirmed removal re-renders the page and leaves the member in its catalog."""
        self.add_permissions("nautobot_dns_models.view_dnszone", "nautobot_dns_models.change_dnszone")
        url = reverse("plugins:nautobot_dns_models:dnszone_remove_from_catalog", kwargs={"pk": self.member_zone.pk})
        response = self.client.post(url, {})
        self.assertHttpStatus(response, 200)
        self.member_zone.refresh_from_db()
        self.assertEqual(self.member_zone.catalog_zone, self.catalog_zone)

    def test_the_remove_page_refuses_a_catalog_the_user_cannot_change(self):
        """The remove page refuses a catalog the user cannot change."""
        permit_zone_change(self.user, self.member_zone)
        url = reverse("plugins:nautobot_dns_models:dnszone_remove_from_catalog", kwargs={"pk": self.member_zone.pk})
        response = self.client.post(url, {"confirm": "true"})

        self.assertRedirects(response, self.catalog_zone.get_absolute_url(), fetch_redirect_response=False)
        self.assertIn(
            "Changing a zone's catalog requires permission to change the catalog zones it is added to or removed from.",
            [str(message) for message in get_messages(response.wsgi_request)],
        )
        self.member_zone.refresh_from_db()
        self.assertEqual(self.member_zone.catalog_zone, self.catalog_zone)

    def test_a_member_the_user_cannot_change_has_no_remove_page(self):
        """A member the user cannot change has no remove page."""
        permit_zone_change(self.user, self.catalog_zone)
        url = reverse("plugins:nautobot_dns_models:dnszone_remove_from_catalog", kwargs={"pk": self.member_zone.pk})
        self.assertHttpStatus(self.client.get(url), 404)

    def test_a_zone_in_no_catalog_has_no_remove_page(self):
        """A zone in no catalog has no remove page."""
        self.add_permissions("nautobot_dns_models.view_dnszone", "nautobot_dns_models.change_dnszone")
        url = reverse("plugins:nautobot_dns_models:dnszone_remove_from_catalog", kwargs={"pk": self.zone.pk})
        self.assertHttpStatus(self.client.get(url), 404)
