"""Unit tests for views."""
# pylint: disable=too-many-lines

from constance import config as constance_config
from django.contrib.auth import get_user_model
from django.test import override_settings
from django.urls import reverse
from nautobot.apps.testing import ViewTestCases
from nautobot.core.testing.utils import extract_page_body
from nautobot.extras.models import Status
from nautobot.ipam.models import IPAddress, Namespace, Prefix
from netutils.ip import ipaddress_address

from nautobot_dns_models.choices import DNSForwardingRuleActionChoices
from nautobot_dns_models.models import (
    AAAARecord,
    ARecord,
    CNAMERecord,
    DNSForwardingRule,
    DNSForwardingRuleIPAddressAssignment,
    DNSRegistrar,
    DNSView,
    DNSZone,
    MXRecord,
    NSRecord,
    PTRRecord,
    SRVRecord,
    TXTRecord,
)
from nautobot_dns_models.tables import DNSForwardingRuleTable

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
        DNSRegistrar.objects.create(name="Registrar 1", url="https://registrar1.example", account_number="ACC-001")
        DNSRegistrar.objects.create(name="Registrar 2", url="https://registrar2.example", account_number="ACC-002")
        DNSRegistrar.objects.create(name="Registrar 3", url="https://registrar3.example", account_number="ACC-003")

        cls.form_data = {
            "name": "Registrar Test",
            "url": "https://registrar-test.example",
            "account_number": "ACC-TEST",
        }

        cls.csv_data = (
            "name,url,account_number",
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

    def _zone(self, name):
        zone = DNSZone(name=name, filename=f"{name}.zone", soa_mname=f"ns1.{name}", soa_rname=f"admin@{name}")
        zone.validated_save()
        return zone

    def _get_detail(self, zone):
        response = self.client.get(zone.get_absolute_url())
        self.assertHttpStatus(response, 200)
        return extract_page_body(response.content.decode(response.charset))

    @override_settings(EXEMPT_VIEW_PERMISSIONS=["*"])
    def test_zone_detail_shows_delegations_children_and_checks(self):
        parent = self._zone("parent.example")
        child = self._zone("apps.parent.example")
        self._zone("lab.parent.example")
        NSRecord.objects.create(zone=parent, name="apps", server="ns1.provider.net")
        NSRecord.objects.create(zone=parent, name="mail", server="ns1.mailvendor.net")
        NSRecord.objects.create(zone=child, name="@", server="ns1.provider.net")

        content = self._get_detail(parent)

        self.assertIn("DELEGATIONS", content)
        self.assertIn("mail.parent.example", content)
        self.assertIn("External", content)
        self.assertIn(child.get_absolute_url(), content)
        self.assertIn("<strong>Child Zones</strong>", content)
        self.assertIn("DELEGATION CHECKS", content)
        self.assertIn("Child zone lab.parent.example has no NS records in this zone", content)

    @override_settings(EXEMPT_VIEW_PERMISSIONS=["*"])
    def test_child_zone_detail_shows_parent_delegation(self):
        parent = self._zone("parent.example")
        child = self._zone("apps.parent.example")
        NSRecord.objects.create(zone=parent, name="apps", server="ns1.provider.net")
        NSRecord.objects.create(zone=child, name="@", server="ns1.provider.net")

        content = self._get_detail(child)

        self.assertIn("PARENT DELEGATION", content)
        self.assertIn(parent.get_absolute_url(), content)
        self.assertIn("ns1.provider.net", content)
        self.assertNotIn("DELEGATION CHECKS", content)

    @override_settings(EXEMPT_VIEW_PERMISSIONS=["*"])
    def test_zone_detail_shows_a_delegation_of_a_name_above_the_zone(self):
        parent = self._zone("parent.example")
        grandchild = self._zone("b.a.parent.example")
        NSRecord.objects.create(zone=parent, name="a", server="ns1.provider.net")

        content = self._get_detail(grandchild)

        self.assertIn("PARENT DELEGATION", content)
        self.assertIn("a.parent.example", content)
        self.assertIn("ns1.provider.net", content)

    @override_settings(EXEMPT_VIEW_PERMISSIONS=["*"])
    def test_zone_detail_hides_delegation_panels_when_empty(self):
        content = self._get_detail(DNSZone.objects.get(name="example-one.com"))

        for label in ("DELEGATIONS", "DELEGATION CHECKS", "PARENT DELEGATION", "<strong>Child Zones</strong>"):
            with self.subTest(label=label):
                self.assertNotIn(label, content)


class DNSForwardingRuleViewTest(ViewTestCases.PrimaryObjectViewTestCase):
    """Test the DNSForwardingRule views."""

    model = DNSForwardingRule

    @staticmethod
    def _formset_data(*rows, initial=0):
        data = {
            "forwarder_assignments-TOTAL_FORMS": str(len(rows)),
            "forwarder_assignments-INITIAL_FORMS": str(initial),
            "forwarder_assignments-MIN_NUM_FORMS": "0",
            "forwarder_assignments-MAX_NUM_FORMS": "1000",
        }
        for index, row in enumerate(rows):
            data.update({f"forwarder_assignments-{index}-{key}": value for key, value in row.items()})
        return data

    @classmethod
    def setUpTestData(cls):
        cls.dns_view = DNSView.objects.get(name="Default")
        status = Status.objects.get(name="Active")
        namespace = Namespace.objects.get(name="Global")
        Prefix.objects.create(prefix="10.0.0.0/24", namespace=namespace, status=status)
        cls.forwarders = [
            IPAddress.objects.create(address=f"10.0.0.{i}/32", namespace=namespace, status=status) for i in (1, 2)
        ]
        cls.unused_ip = IPAddress.objects.create(address="10.0.0.9/32", namespace=namespace, status=status)

        DNSForwardingRule.objects.create(name="corp.example.com", dns_view=cls.dns_view)
        DNSForwardingRule.objects.create(name="partner.example.net", dns_view=cls.dns_view)
        DNSForwardingRule.objects.create(name="lab.example.org", dns_view=cls.dns_view)

        cls.form_data = {
            "name": "new.example.com",
            "dns_view": cls.dns_view.pk,
            "action": DNSForwardingRuleActionChoices.ACTION_FORWARD_ONLY,
            "enabled": True,
            "description": "New rule",
            **cls._formset_data({"ip_address": cls.forwarders[0].pk, "port": 5353, "weight": 10}),
        }
        cls.csv_data = (
            "name,dns_view,action",
            f"csv.example.com,{cls.dns_view.pk},forward_only",
            f"csv.example.net,{cls.dns_view.pk},do_not_forward",
        )
        cls.bulk_edit_data = {
            "action": DNSForwardingRuleActionChoices.ACTION_FORWARD_ONLY,
            "description": "Bulk edited",
        }

    def _add_edit_permissions(self):
        self.add_permissions(
            "nautobot_dns_models.add_dnsforwardingrule",
            "nautobot_dns_models.change_dnsforwardingrule",
            "nautobot_dns_models.view_dnsforwardingrule",
            "nautobot_dns_models.view_dnsview",
            "ipam.view_ipaddress",
        )

    def test_create_rule_with_forwarders(self):
        self._add_edit_permissions()
        data = {
            "name": "ad.example.com",
            "dns_view": self.dns_view.pk,
            "action": DNSForwardingRuleActionChoices.ACTION_FORWARD_ONLY,
            **self._formset_data(
                {"ip_address": self.forwarders[0].pk, "port": 53, "weight": 20},
                {"ip_address": self.forwarders[1].pk, "port": 5353, "weight": 10},
            ),
        }

        response = self.client.post(self._get_url("add"), data=data)

        self.assertHttpStatus(response, 302)
        rule = DNSForwardingRule.objects.get(name="ad.example.com")
        self.assertEqual(
            [(a.ip_address, a.port, a.weight) for a in rule.forwarder_assignments.all()],
            [(self.forwarders[1], 5353, 10), (self.forwarders[0], 53, 20)],
        )

    def test_edit_rule_removes_deleted_forwarder(self):
        self._add_edit_permissions()
        rule = DNSForwardingRule.objects.get(name="corp.example.com")
        assignment = DNSForwardingRuleIPAddressAssignment.objects.create(
            forwarding_rule=rule, ip_address=self.forwarders[0]
        )
        data = {
            "name": rule.name,
            "dns_view": self.dns_view.pk,
            "action": rule.action,
            **self._formset_data(
                {
                    "id": assignment.pk,
                    "forwarding_rule": rule.pk,
                    "ip_address": self.forwarders[0].pk,
                    "port": 53,
                    "weight": 100,
                    "DELETE": "on",
                },
                initial=1,
            ),
        }

        response = self.client.post(self._get_url("edit", rule), data=data)

        self.assertHttpStatus(response, 302)
        self.assertFalse(rule.forwarder_assignments.exists())

    def test_invalid_forwarder_on_update_reverts_the_rule_changes(self):
        self._add_edit_permissions()
        rule = DNSForwardingRule.objects.get(name="corp.example.com")
        data = {
            "name": rule.name,
            "dns_view": self.dns_view.pk,
            "action": rule.action,
            "description": "Changed",
            **self._formset_data({"ip_address": self.forwarders[0].pk, "port": 70000, "weight": 100}),
        }

        response = self.client.post(self._get_url("edit", rule), data=data)

        self.assertHttpStatus(response, 200)
        rule.refresh_from_db()
        self.assertEqual(rule.description, "")
        self.assertFalse(rule.forwarder_assignments.exists())

    def test_forwarder_must_be_an_ip_address_the_user_can_view(self):
        self._add_edit_permissions()
        self.remove_permissions("ipam.view_ipaddress")
        self.add_permissions("ipam.view_ipaddress", constraints={"host": "10.0.0.1"})
        data = {
            "name": "restricted.example.com",
            "dns_view": self.dns_view.pk,
            "action": DNSForwardingRuleActionChoices.ACTION_FORWARD_ONLY,
            **self._formset_data({"ip_address": self.forwarders[1].pk, "port": 53, "weight": 100}),
        }

        response = self.client.post(self._get_url("add"), data=data)

        self.assertHttpStatus(response, 200)
        self.assertFalse(DNSForwardingRule.objects.filter(name="restricted.example.com").exists())

        data["forwarder_assignments-0-ip_address"] = self.forwarders[0].pk
        self.assertHttpStatus(self.client.post(self._get_url("add"), data=data), 302)
        self.assertEqual(
            list(DNSForwardingRule.objects.get(name="restricted.example.com").forwarders.all()), [self.forwarders[0]]
        )

    def test_invalid_forwarder_rolls_back_the_rule(self):
        self._add_edit_permissions()
        data = {
            "name": "public.example.net",
            "dns_view": self.dns_view.pk,
            "action": DNSForwardingRuleActionChoices.ACTION_DO_NOT_FORWARD,
            **self._formset_data({"ip_address": self.forwarders[0].pk, "port": 53, "weight": 100}),
        }

        response = self.client.post(self._get_url("add"), data=data)

        self.assertHttpStatus(response, 200)
        self.assertIn(
            "Forwarder 1: A rule with the action Do not forward cannot have forwarders.",
            extract_page_body(response.content.decode(response.charset)),
        )
        self.assertFalse(DNSForwardingRule.objects.filter(name="public.example.net").exists())

    @override_settings(EXEMPT_VIEW_PERMISSIONS=["*"])
    def test_detail_view_shows_forwarders_and_rule_checks(self):
        rule = DNSForwardingRule.objects.get(name="partner.example.net")
        empty_rule = DNSForwardingRule.objects.get(name="corp.example.com")
        DNSForwardingRuleIPAddressAssignment.objects.create(
            forwarding_rule=rule, ip_address=self.forwarders[1], port=5353
        )

        content = extract_page_body(self.client.get(rule.get_absolute_url()).content.decode())
        self.assertIn(self.forwarders[1].get_absolute_url(), content)
        self.assertIn("5353", content)
        self.assertNotIn("RULE CHECKS", content)

        content = extract_page_body(self.client.get(empty_rule.get_absolute_url()).content.decode())
        self.assertIn("RULE CHECKS", content)
        self.assertIn("No forwarders are assigned", content)

    @override_settings(EXEMPT_VIEW_PERMISSIONS=["*"])
    def test_ipaddress_detail_lists_forwarding_rules_only_when_used(self):
        rule = DNSForwardingRule.objects.get(name="corp.example.com")
        DNSForwardingRuleIPAddressAssignment.objects.create(forwarding_rule=rule, ip_address=self.forwarders[0])
        panel_title = "<strong>DNS Forwarding Rules</strong>"

        content = extract_page_body(self.client.get(self.forwarders[0].get_absolute_url()).content.decode())
        self.assertInHTML(panel_title, content, 1)
        self.assertIn(rule.get_absolute_url(), content)

        content = extract_page_body(self.client.get(self.unused_ip.get_absolute_url()).content.decode())
        self.assertInHTML(panel_title, content, 0)

    @override_settings(EXEMPT_VIEW_PERMISSIONS=["*"])
    def test_forwarder_on_two_ports_is_listed_once(self):
        rule = DNSForwardingRule.objects.get(name="corp.example.com")
        for port in (53, 5353):
            DNSForwardingRuleIPAddressAssignment.objects.create(
                forwarding_rule=rule, ip_address=self.forwarders[0], port=port
            )

        ip_page = extract_page_body(self.client.get(self.forwarders[0].get_absolute_url()).content.decode())
        table = DNSForwardingRuleTable(DNSForwardingRule.objects.filter(pk=rule.pk))
        forwarders_cell = table.columns["forwarders"].column.render(rule.forwarders)

        self.assertEqual(ip_page.count(f'href="{rule.get_absolute_url()}"'), 1)
        self.assertEqual(forwarders_cell.count(f'href="{self.forwarders[0].get_absolute_url()}"'), 1)

    def test_ipaddress_detail_hides_forwarding_rules_the_user_cannot_view(self):
        self.add_permissions("ipam.view_ipaddress")
        rule = DNSForwardingRule.objects.get(name="corp.example.com")
        DNSForwardingRuleIPAddressAssignment.objects.create(forwarding_rule=rule, ip_address=self.forwarders[0])

        content = extract_page_body(self.client.get(self.forwarders[0].get_absolute_url()).content.decode())

        self.assertInHTML("<strong>DNS Forwarding Rules</strong>", content, 0)


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
