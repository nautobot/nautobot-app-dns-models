"""Test DNSZone."""
# pylint: disable=too-many-lines

import importlib

from constance.test import override_config
from django.apps import apps as django_apps
from django.core.exceptions import ValidationError
from django.db import connection
from django.test.utils import CaptureQueriesContext
from nautobot.apps.testing import ModelTestCases, TestCase
from nautobot.extras.models import Status
from nautobot.ipam.models import IPAddress, Namespace, Prefix
from netutils.ip import ipaddress_address

from nautobot_dns_models.choices import DNSForwardingRuleActionChoices
from nautobot_dns_models.models import (
    UINT32_MAX,
    AAAARecord,
    ARecord,
    CNAMERecord,
    DNSForwardingRule,
    DNSForwardingRuleIPAddressAssignment,
    DNSRegistrar,
    DNSView,
    DNSViewPrefixAssignment,
    DNSZone,
    MXRecord,
    NSRecord,
    PTRRecord,
    SRVRecord,
    TXTRecord,
    dns_wire_label_length,
)


# Helper for generating unicode labels of a specific IDNA-encoded length
def _make_unicode_label_with_idna_length(char, target_length):
    """Return a string of repeated `char` whose IDNA-encoded length is exactly `target_length` bytes."""
    label = ""
    while dns_wire_label_length(label) < target_length:
        label += char
    if dns_wire_label_length(label) > target_length:
        label = label[:-1]
    if dns_wire_label_length(label) != target_length:
        raise ValueError(f"Could not generate label of exactly {target_length} bytes in IDNA.")
    return label


class TestDNSView(ModelTestCases.BaseModelTestCase):
    """Test DNSView model."""

    model = DNSView

    @classmethod
    def setUpTestData(cls):
        """Create test data for DNSView Model."""
        super().setUpTestData()
        # Create 3 objects for the model test cases.
        DNSView.objects.create(name="View 1", description="First DNS View")
        DNSView.objects.create(name="View 2", description="Second DNS View")
        DNSView.objects.create(name="View 3", description="Third DNS View")

    def test_create_dnsview_only_required(self):
        """Create with only required fields, and validate null description and __str__."""
        dnsview = DNSView.objects.create(name="Test View")
        self.assertEqual(dnsview.name, "Test View")
        self.assertEqual(dnsview.description, "")
        self.assertEqual(str(dnsview), "Test View")

    def test_create_dnsview_all_fields_success(self):
        """Create DNSViewModel with all fields."""
        dnsview = DNSView.objects.create(name="Test View", description="Test Description")
        self.assertEqual(dnsview.name, "Test View")
        self.assertEqual(dnsview.description, "Test Description")

    def test_get_absolute_url(self):
        dns_view_model = DNSView.objects.get(name="View 1")
        self.assertEqual(dns_view_model.get_absolute_url(), f"/plugins/dns/dns-views/{dns_view_model.id}/")


class TestDNSViewPrefixAssignment(ModelTestCases.BaseModelTestCase):
    """Test DNSViewPrefixAssignment model."""

    model = DNSViewPrefixAssignment

    @classmethod
    def setUpTestData(cls):
        """Create test data for DNSViewPrefixAssignment Model."""
        super().setUpTestData()
        # Create Prefixes
        status = Status.objects.get(name="Active")
        namespace = Namespace.objects.get(name="Global")
        cls.prefixes = (
            Prefix.objects.create(prefix="10.0.0.0/24", namespace=namespace, status=status),
            Prefix.objects.create(prefix="2001:db8:abcd:99::/64", namespace=namespace, status=status),
        )
        # Create DNS Views
        cls.dns_views = (
            DNSView.objects.create(name="View 1", description="First DNS View"),
            DNSView.objects.create(name="View 2", description="Second DNS View"),
        )

        # Create DNSViewPrefixAssignment
        DNSViewPrefixAssignment.objects.create(dns_view=cls.dns_views[0], prefix=cls.prefixes[0])

    def test_create_dnsviewprefixassignment(self):
        """Create DNSViewPrefixAssignment with all fields."""
        assignment = DNSViewPrefixAssignment.objects.create(dns_view=self.dns_views[1], prefix=self.prefixes[1])
        self.assertEqual(assignment.dns_view, self.dns_views[1])
        self.assertEqual(assignment.prefix, self.prefixes[1])


class TestDNSRegistrar(ModelTestCases.BaseModelTestCase):
    """Test DNSRegistrar model."""

    model = DNSRegistrar

    @classmethod
    def setUpTestData(cls):
        """Create test data for DNSRegistrar Model."""
        super().setUpTestData()
        DNSRegistrar.objects.create(name="Registrar 1", url="https://registrar1.example", account_number="ACC-001")
        DNSRegistrar.objects.create(name="Registrar 2", url="https://registrar2.example", account_number="ACC-002")
        DNSRegistrar.objects.create(name="Registrar 3", url="https://registrar3.example", account_number="ACC-003")

    def test_create_dnsregistrar_only_required(self):
        """Create with only required fields."""
        registrar = DNSRegistrar.objects.create(name="Test Registrar")
        self.assertEqual(registrar.name, "Test Registrar")
        self.assertEqual(registrar.url, "")
        self.assertEqual(registrar.account_number, "")
        self.assertEqual(str(registrar), "Test Registrar")

    def test_create_dnsregistrar_all_fields_success(self):
        """Create DNSRegistrar with all fields."""
        registrar = DNSRegistrar.objects.create(
            name="Another Registrar",
            url="https://another-registrar.example",
            account_number="ACCT-1234",
        )
        self.assertEqual(registrar.name, "Another Registrar")
        self.assertEqual(registrar.url, "https://another-registrar.example")
        self.assertEqual(registrar.account_number, "ACCT-1234")

    def test_get_absolute_url(self):
        registrar = DNSRegistrar.objects.get(name="Registrar 1")
        self.assertEqual(registrar.get_absolute_url(), f"/plugins/dns/dns-registrars/{registrar.id}/")


class TestDnsZone(ModelTestCases.BaseModelTestCase):
    """Test DnsZone model."""

    model = DNSZone

    @classmethod
    def setUpTestData(cls):
        """Create test data for DNSZone Model."""
        super().setUpTestData()
        # Create 3 objects for the model test cases.
        DNSZone.objects.create(name="Test One")
        DNSZone.objects.create(name="Test Two")
        DNSZone.objects.create(name="Test Three")

    def test_create_dnszone_only_required(self):
        """Create with only required fields, and validate null description and __str__."""
        dnszone = DNSZone.objects.create(name="Development")
        self.assertEqual(dnszone.name, "Development")
        self.assertEqual(dnszone.description, "")
        self.assertTrue(dnszone.enabled)
        self.assertEqual(str(dnszone), "Development (Default)")

    def test_create_dnszone_all_fields_success(self):
        """Create DnsZoneModel with all fields."""
        dnszone = DNSZone.objects.create(
            name="Development",
            description="Development Test",
            filename="development.zone",
            soa_mname="ns1.development.example",
            soa_rname="admin@development.example",
        )
        self.assertEqual(dnszone.name, "Development")
        self.assertEqual(dnszone.description, "Development Test")
        self.assertEqual(dnszone.filename, "development.zone")

    def test_get_absolute_url(self):
        dns_zone_model = DNSZone.objects.create(name="example.com")
        self.assertEqual(dns_zone_model.get_absolute_url(), f"/plugins/dns/dns-zones/{dns_zone_model.id}/")


class NSRecordTestCase(TestCase):
    """Test the NSRecord model."""

    @classmethod
    def setUpTestData(cls):
        cls.dns_zone = DNSZone.objects.create(name="example.com")

    def test_create_nsrecord(self):
        ns_record = NSRecord.objects.create(name="primary", server="example-server.com.", zone=self.dns_zone)

        self.assertEqual(ns_record.name, "primary")
        self.assertEqual(ns_record.server, "example-server.com.")
        self.assertEqual(str(ns_record), ns_record.name)

    def test_get_absolute_url(self):
        ns_record = NSRecord.objects.create(name="primary", server="example-server.com.", zone=self.dns_zone)
        self.assertEqual(ns_record.get_absolute_url(), f"/plugins/dns/ns-records/{ns_record.id}/")


class ARecordTestCase(TestCase):
    """Test the ARecord model."""

    @classmethod
    def setUpTestData(cls):
        cls.dns_zone = DNSZone.objects.create(name="example.com")
        status = Status.objects.get(name="Active")
        namespace = Namespace.objects.get(name="Global")
        Prefix.objects.create(prefix="10.0.0.0/24", namespace=namespace, type="Pool", status=status)
        cls.ip_address = IPAddress.objects.create(address="10.0.0.1/32", namespace=namespace, status=status)
        # IPv6 Test data
        Prefix.objects.create(prefix="2001:db8:abcd:99::/64", namespace=namespace, type="Pool", status=status)
        cls.ipv6_address = IPAddress.objects.create(
            address="2001:db8:abcd:99::1/128", namespace=namespace, status=status
        )

    def test_create_arecord(self):
        a_record = ARecord.objects.create(name="site.example.com", ip_address=self.ip_address, zone=self.dns_zone)

        self.assertEqual(a_record.name, "site.example.com")
        self.assertEqual(a_record.ip_address, self.ip_address)
        self.assertEqual(a_record.ttl, 3600)
        self.assertEqual(str(a_record), a_record.name)

    def test_create_ipv6_arecord_fails(self):
        # Test that creating an IPv6 Address fails
        with self.assertRaises(ValidationError):
            invalid_record = ARecord(name="invalid.example.com", ip_address=self.ipv6_address, zone=self.dns_zone)
            invalid_record.full_clean()

    def test_create_ipv6_arecord_fails_on_save(self):
        """Creating via ORM should also fail due to save() calling clean()."""
        with self.assertRaises(ValidationError):
            ARecord.objects.create(name="invalid-save.example.com", ip_address=self.ipv6_address, zone=self.dns_zone)

    def test_get_absolute_url(self):
        a_record = ARecord.objects.create(name="site.example.com", ip_address=self.ip_address, zone=self.dns_zone)
        self.assertEqual(a_record.get_absolute_url(), f"/plugins/dns/a-records/{a_record.id}/")


class AAAARecordTestCase(TestCase):
    """Test the AAAARecord model."""

    @classmethod
    def setUpTestData(cls):
        cls.dns_zone = DNSZone.objects.create(name="example.com")
        status = Status.objects.get(name="Active")
        namespace = Namespace.objects.get(name="Global")
        Prefix.objects.create(prefix="2001:db8:abcd:12::/64", namespace=namespace, type="Pool", status=status)
        cls.ip_address = IPAddress.objects.create(address="2001:db8:abcd:12::1/128", namespace=namespace, status=status)
        # IPv4 Test Data
        Prefix.objects.create(prefix="10.1.0.0/24", namespace=namespace, type="Pool", status=status)
        cls.ipv4_address = IPAddress.objects.create(address="10.1.0.1/32", namespace=namespace, status=status)

    def test_create_aaaarecord(self):
        aaaa_record = AAAARecord.objects.create(name="site.example.com", ip_address=self.ip_address, zone=self.dns_zone)

        self.assertEqual(aaaa_record.name, "site.example.com")
        self.assertEqual(aaaa_record.ip_address, self.ip_address)
        self.assertEqual(aaaa_record.ttl, 3600)
        self.assertEqual(str(aaaa_record), aaaa_record.name)

    def test_create_ipv4_aaaarecord_fails(self):
        # Test that creating an IPv4 Address fails
        with self.assertRaises(ValidationError):
            invalid_record = AAAARecord(name="invalid.example.com", ip_address=self.ipv4_address, zone=self.dns_zone)
            invalid_record.full_clean()

    def test_create_ipv4_aaaarecord_fails_on_save(self):
        """Creating via ORM should also fail due to save() calling clean()."""
        with self.assertRaises(ValidationError):
            AAAARecord.objects.create(
                name="invalid-save.example.com",
                ip_address=self.ipv4_address,
                zone=self.dns_zone,
            )

    def test_get_absolute_url(self):
        aaaa_record = AAAARecord.objects.create(name="site.example.com", ip_address=self.ip_address, zone=self.dns_zone)
        self.assertEqual(aaaa_record.get_absolute_url(), f"/plugins/dns/aaaa-records/{aaaa_record.id}/")


class CNAMERecordTestCase(TestCase):
    """Test the CNAMERecord model."""

    @classmethod
    def setUpTestData(cls):
        cls.dns_zone = DNSZone.objects.create(name="example.com")

    def test_create_cnamerecord(self):
        cname_record = CNAMERecord.objects.create(name="www.example.com", alias="site.example.com", zone=self.dns_zone)

        self.assertEqual(cname_record.name, "www.example.com")
        self.assertEqual(cname_record.alias, "site.example.com")
        self.assertEqual(str(cname_record), cname_record.name)

    def test_get_absolute_url(self):
        cname_record = CNAMERecord.objects.create(name="www.example.com", alias="site.example.com", zone=self.dns_zone)
        self.assertEqual(cname_record.get_absolute_url(), f"/plugins/dns/cname-records/{cname_record.id}/")


class MXRecordTestCase(TestCase):
    """Test the MXRecord model."""

    @classmethod
    def setUpTestData(cls):
        cls.dns_zone = DNSZone.objects.create(name="example.com")

    def test_create_mxrecord(self):
        mx_record = MXRecord.objects.create(name="mail-record", mail_server="mail.example.com", zone=self.dns_zone)

        self.assertEqual(mx_record.name, "mail-record")
        self.assertEqual(mx_record.preference, 10)
        self.assertEqual(mx_record.mail_server, "mail.example.com")
        self.assertEqual(str(mx_record), mx_record.name)

    def test_get_absolute_url(self):
        mx_record = MXRecord.objects.create(name="mail-record", mail_server="mail.example.com", zone=self.dns_zone)
        self.assertEqual(mx_record.get_absolute_url(), f"/plugins/dns/mx-records/{mx_record.id}/")


class TXTRecordTestCase(TestCase):
    """Test the TXTRecord model."""

    @classmethod
    def setUpTestData(cls):
        cls.dns_zone = DNSZone.objects.create(name="example.com")

    def test_create_txtrecord(self):
        txt_record = TXTRecord.objects.create(name="txt-record", text="spf-record", zone=self.dns_zone)

        self.assertEqual(txt_record.name, "txt-record")
        self.assertEqual(txt_record.text, "spf-record")
        self.assertEqual(str(txt_record), txt_record.name)

    def test_get_absolute_url(self):
        txt_record = TXTRecord.objects.create(name="txt-record", text="spf-record", zone=self.dns_zone)
        self.assertEqual(txt_record.get_absolute_url(), f"/plugins/dns/txt-records/{txt_record.id}/")


class PTRRecordTestCase(TestCase):
    """Test the PTRRecord model."""

    @classmethod
    def setUpTestData(cls):
        cls.dns_zone = DNSZone.objects.create(name="example.com")

    def test_create_ptrrecord(self):
        ptr_record = PTRRecord.objects.create(name="ptr-record", ptrdname="ptr-record", zone=self.dns_zone)

        self.assertEqual(ptr_record.ptrdname, "ptr-record")
        self.assertEqual(str(ptr_record), ptr_record.ptrdname)

    def test_get_absolute_url(self):
        ptr_record = PTRRecord.objects.create(ptrdname="ptr-record", zone=self.dns_zone)
        self.assertEqual(ptr_record.get_absolute_url(), f"/plugins/dns/ptr-records/{ptr_record.id}/")


class SRVRecordTestCase(TestCase):
    """Test the SRVRecord model."""

    @classmethod
    def setUpTestData(cls):
        cls.dns_zone = DNSZone.objects.create(name="example.com", ttl=7200)

    def test_create_srvrecord(self):
        srv_record = SRVRecord.objects.create(
            name="_sip._tcp.example.com",
            priority=10,
            weight=5,
            port=5060,
            target="sip.example.com",
            zone=self.dns_zone,
            ttl=3600,
            description="SIP server",
            comment="Primary SIP server",
        )

        self.assertEqual(srv_record.name, "_sip._tcp.example.com")
        self.assertEqual(srv_record.priority, 10)
        self.assertEqual(srv_record.weight, 5)
        self.assertEqual(srv_record.port, 5060)
        self.assertEqual(srv_record.target, "sip.example.com")
        self.assertEqual(srv_record.ttl, 3600)
        self.assertEqual(srv_record.description, "SIP server")
        self.assertEqual(srv_record.comment, "Primary SIP server")
        self.assertEqual(str(srv_record), srv_record.name)

    def test_create_srvrecord_wo_ttl(self):
        srv_record = SRVRecord.objects.create(
            name="_sip._tcp.example.com",
            priority=10,
            weight=5,
            port=5060,
            target="sip.example.com",
            zone=self.dns_zone,
            description="SIP server",
            comment="Primary SIP server",
        )

        self.assertEqual(srv_record.name, "_sip._tcp.example.com")
        self.assertEqual(srv_record.priority, 10)
        self.assertEqual(srv_record.weight, 5)
        self.assertEqual(srv_record.port, 5060)
        self.assertEqual(srv_record.target, "sip.example.com")
        self.assertEqual(srv_record.ttl, 7200)  # Inherits from DNSZone
        self.assertEqual(srv_record.description, "SIP server")
        self.assertEqual(srv_record.comment, "Primary SIP server")
        self.assertEqual(str(srv_record), srv_record.name)

    def test_get_absolute_url(self):
        srv_record = SRVRecord.objects.create(
            name="_sip._tcp.example.com", priority=10, weight=5, port=5060, target="sip.example.com", zone=self.dns_zone
        )
        self.assertEqual(srv_record.get_absolute_url(), f"/plugins/dns/srv-records/{srv_record.id}/")


@override_config(nautobot_dns_models__CNAME_RESTRICTION_ENABLED=True)
class CNAMEExclusivityModelTestCase(TestCase):
    """Model-level tests for exact-match CNAME exclusivity."""

    @classmethod
    def setUpTestData(cls):
        cls.zone = DNSZone.objects.create(name="example.com")
        # IP setup for ARecord use
        status = Status.objects.get(name="Active")
        namespace = Namespace.objects.get(name="Global")
        Prefix.objects.create(prefix="10.9.0.0/24", namespace=namespace, type="Pool", status=status)
        cls.ipv4_1 = IPAddress.objects.create(address="10.9.0.1/32", namespace=namespace, status=status)
        cls.ipv4_2 = IPAddress.objects.create(address="10.9.0.2/32", namespace=namespace, status=status)

    def test_cname_blocked_when_arecord_exists(self):
        ARecord.objects.create(name="app", ip_address=self.ipv4_1, zone=self.zone)
        with self.assertRaises(ValidationError):
            cname_record = CNAMERecord(name="app", alias="target.example.com", zone=self.zone)
            cname_record.validated_save()

    def test_non_cname_blocked_when_cname_exists(self):
        CNAMERecord.objects.create(name="web", alias="web.example.com", zone=self.zone)
        # TODO: remove `save` overwrite from ARecord model and revisit this test
        with self.assertRaises(ValidationError):
            ARecord.objects.create(name="web", ip_address=self.ipv4_2, zone=self.zone)

    def test_zone_qualified_name_allowed(self):
        """A(name='host') does NOT block CNAME(name='host.zone') since names must match exactly."""
        ARecord.objects.create(name="testrecord", ip_address=self.ipv4_1, zone=self.zone)
        # Allowed because name differs (zone-qualified vs relative)
        CNAMERecord.objects.create(name=f"testrecord.{self.zone.name}", alias="x.example.com", zone=self.zone)

    def test_trailing_dot_zone_qualified_allowed(self):
        """A(name='host') does NOT block CNAME(name='host.zone.') (trailing dot normalized)."""
        ARecord.objects.create(name="td", ip_address=self.ipv4_1, zone=self.zone)
        # Trailing dot is removed to "td.zone", still zone-qualified and thus different from "td"
        CNAMERecord.objects.create(name=f"td.{self.zone.name}.", alias="x.example.com", zone=self.zone)

    @override_config(nautobot_dns_models__CNAME_RESTRICTION_ENABLED=False)
    def test_opt_out_allows_coexistence(self):
        ARecord.objects.create(name="opt", ip_address=self.ipv4_1, zone=self.zone)
        # Should succeed when enforcement disabled
        CNAMERecord.objects.create(name="opt", alias="opt.example.com", zone=self.zone)


class DNSRecordNameLengthValidationTest(TestCase):
    """Test DNS record name validation rules from RFC 1035 §3.1."""

    @classmethod
    def setUpTestData(cls):
        cls.zone = DNSZone.objects.create(name="example.com")

    # ASCII Label Tests
    def test_accepts_valid_ascii_label(self):
        record = TXTRecord(name="www", text="test", zone=self.zone)
        record.full_clean()  # Should not raise
        record = TXTRecord(name="www.subdomain", text="test", zone=self.zone)
        record.full_clean()  # Should not raise

    def test_accepts_ascii_label_of_63_bytes(self):
        label_63 = "a" * 63
        record = TXTRecord(name=label_63, text="test", zone=self.zone)
        record.full_clean()  # Should not raise

    def test_rejects_ascii_label_of_64_bytes(self):
        label_64 = "a" * 64
        record = TXTRecord(name=label_64, text="test", zone=self.zone)
        with self.assertRaises(ValidationError) as context:
            record.full_clean()
        self.assertIn(
            f"Label '{label_64}' exceeds the maximum length of 63 bytes (octets) in wire format", str(context.exception)
        )

    # Unicode Label Tests
    def test_accepts_valid_unicode_label(self):
        label = "ü"
        record = TXTRecord(name=label, text="test", zone=self.zone)
        record.full_clean()  # Should not raise

    def test_accepts_unicode_label_of_63_idna_bytes(self):
        label = _make_unicode_label_with_idna_length("ü", 63)
        record = TXTRecord(name=label, text="test", zone=self.zone)
        record.full_clean()  # Should not raise

    def test_rejects_unicode_label_exceeding_63_idna_bytes(self):
        label = _make_unicode_label_with_idna_length("ü", 63) + "ü"
        record = TXTRecord(name=label, text="test", zone=self.zone)
        with self.assertRaises(ValidationError) as context:
            record.full_clean()
        self.assertIn(
            f"Label '{label}' exceeds the maximum length of 63 bytes (octets) in wire format", str(context.exception)
        )

    # Enforcement Flag Tests
    @override_config(nautobot_dns_models__DNS_VALIDATION_LEVEL=False)
    def test_accepts_label_exceeding_63_bytes_when_enforcement_disabled(self):
        record = TXTRecord(name="a" * 64, text="test", zone=self.zone)
        record.full_clean()  # Should not raise

    def test_rejects_label_exceeding_63_bytes_when_enforcement_enabled(self):
        record = TXTRecord(name="a" * 64, text="test", zone=self.zone)
        with self.assertRaises(ValidationError) as context:
            record.full_clean()
        self.assertIn(
            "Label 'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa' exceeds the maximum length of 63 bytes (octets) in wire format",
            str(context.exception),
        )

    # FQDN Length Tests
    @override_config(nautobot_dns_models__DNS_VALIDATION_LEVEL=False)
    def test_accepts_fqdn_exceeding_255_bytes_when_enforcement_disabled(self):
        zone = DNSZone.objects.create(
            name="x" * 63, filename="x" * 63 + ".zone", soa_mname="ns1." + "x" * 63 + ".", soa_rname="admin@example.com"
        )
        record = TXTRecord(name="x" * 63 + "." + "x" * 63 + "." + "x" * 63, text="test", zone=zone)
        record.full_clean()  # Should not raise

    def test_rejects_fqdn_exceeding_255_bytes_when_enforcement_enabled(self):
        zone_label = "z" * 63
        zone = DNSZone.objects.create(
            name=zone_label,
            filename=zone_label + ".zone",
            soa_mname="ns1." + zone_label + ".",
            soa_rname="admin@example.com",
        )
        record = TXTRecord(name="a" * 63 + "." + "b" * 63, text="test", zone=zone)
        record.full_clean()  # Should not raise
        record = TXTRecord(name="a" * 63 + "." + "b" * 63 + "." + "c" * 63, text="test", zone=zone)
        with self.assertRaises(ValidationError) as context:
            record.full_clean()
        self.assertIn(
            "Total length of DNS name cannot exceed 255 bytes (octets) in wire format", str(context.exception)
        )

    # Structure/Format Tests
    def test_rejects_empty_label(self):
        record = TXTRecord(name="www..subdomain", text="test", zone=self.zone)
        with self.assertRaises(ValidationError) as context:
            record.full_clean()
        self.assertIn("Empty labels are not allowed", str(context.exception))

    def test_rejects_label_with_leading_or_trailing_dot(self):
        # Leading dot
        record = TXTRecord(name=".example", text="test", zone=self.zone)
        with self.assertRaises(ValidationError) as context:
            record.full_clean()
        self.assertIn("Empty labels are not allowed", str(context.exception))
        # Trailing dot
        record = TXTRecord(name="example.", text="test", zone=self.zone)
        with self.assertRaises(ValidationError) as context:
            record.full_clean()
        self.assertIn("Empty labels are not allowed", str(context.exception))


class DNSZoneSOARNameTest(TestCase):
    """Test SOA RNAME normalization and validation."""

    def test_save_normalizes_soa_rname(self):
        test_cases = {
            "john.example.com": "john@example.com",
            "john.example.com.": "john@example.com",
            r"john\.smith.example.com": "john.smith@example.com",
            r"john\.smith.example.com.": "john.smith@example.com",
            r"john_smith.example.com": "john_smith@example.com",
            r"john_smith.example.com.": "john_smith@example.com",
            "invalid": "invalid",
            "invalid.": "invalid",
        }
        for index, (value, expected) in enumerate(test_cases.items()):
            with self.subTest(value=value):
                zone = DNSZone.objects.create(
                    name=f"rname-{index}.example",
                    filename=f"rname-{index}.example.zone",
                    soa_mname=f"ns1.rname-{index}.example.",
                    soa_rname=value,
                )
                self.assertEqual(zone.soa_rname, expected)

    def test_save_rejects_invalid_soa_rname(self):
        invalid_values = (
            "",
            "john@example",
            "john.example",
            "john@",
            "@example.com",
            "john@@example.com",
            ".example.com",
            "john..example.com",
            r"john\\.smith.example.com",
            r"john\\.smith.example.com.",
            r"john\\\.smith.example.com",
            r"john\\\.smith.example.com.",
            r"john\046example.com.",
            r"john.example\.com.",
            "a" * 64,
        )
        for index, value in enumerate(invalid_values):
            with self.subTest(value=value):
                zone = DNSZone(
                    name=f"invalid-rname-{index}.example",
                    filename=f"invalid-rname-{index}.example.zone",
                    soa_mname=f"ns1.invalid-rname-{index}.example.",
                    soa_rname=value,
                )

                with self.assertRaises(ValidationError) as context:
                    zone.validated_save()

                self.assertIn("soa_rname", context.exception.message_dict)


class DNSZoneNameLengthValidationTest(TestCase):
    """Test DNS zone name validation rules from RFC 1035 §3.1.

    Note: We don't test wire format length for zones because the model's CharField
    max_length=200 constraint is stricter than the DNS wire format limit of 255 octets.
    The wire format test is only needed for records, which can have longer names
    when combined with their zone.
    """

    @classmethod
    def setUpTestData(cls):
        cls.zone = DNSZone.objects.create(name="example.com")

    # ASCII Label Tests
    def test_accepts_valid_ascii_label(self):
        zone = DNSZone(name="test1", filename="test1.zone", soa_mname="ns1.test1.", soa_rname="admin@example.com")
        zone.full_clean()  # Should not raise
        zone = DNSZone(
            name="test2.example.com",
            filename="test2.example.com.zone",
            soa_mname="ns1.test2.example.com.",
            soa_rname="admin@example.com",
        )
        zone.full_clean()  # Should not raise

    def test_accepts_ascii_label_of_63_bytes(self):
        label_63 = "a" * 63
        zone = DNSZone(
            name=label_63,
            filename=label_63 + ".zone",
            soa_mname="ns1." + label_63 + ".",
            soa_rname="admin@example.com",
        )
        zone.full_clean()  # Should not raise

    def test_rejects_ascii_label_of_64_bytes(self):
        label_64 = "a" * 64
        zone = DNSZone(
            name=label_64,
            filename=label_64 + ".zone",
            soa_mname="ns1." + label_64 + ".",
            soa_rname="admin@example.com",
        )
        with self.assertRaises(ValidationError) as context:
            zone.full_clean()
        self.assertIn(
            f"Label '{label_64}' exceeds the maximum length of 63 bytes (octets) in wire format", str(context.exception)
        )

    # Unicode Label Tests
    def test_accepts_valid_unicode_label(self):
        label = "ü"
        zone = DNSZone(
            name=label,
            filename=label + ".zone",
            soa_mname="ns1." + label + ".",
            soa_rname="admin@example.com",
        )
        zone.full_clean()  # Should not raise

    def test_accepts_unicode_label_of_63_idna_bytes(self):
        label = _make_unicode_label_with_idna_length("ü", 63)
        zone = DNSZone(
            name=label,
            filename=label + ".zone",
            soa_mname="ns1." + label + ".",
            soa_rname="admin@example.com",
        )
        zone.full_clean()  # Should not raise

    def test_rejects_unicode_label_exceeding_63_idna_bytes(self):
        label = _make_unicode_label_with_idna_length("ü", 63) + "ü"
        zone = DNSZone(
            name=label,
            filename=label + ".zone",
            soa_mname="ns1." + label + ".",
            soa_rname="admin@example.com",
        )
        with self.assertRaises(ValidationError) as context:
            zone.full_clean()
        self.assertIn(
            f"Label '{label}' exceeds the maximum length of 63 bytes (octets) in wire format", str(context.exception)
        )

    # Enforcement Flag Tests
    @override_config(nautobot_dns_models__DNS_VALIDATION_LEVEL=False)
    def test_accepts_label_exceeding_63_bytes_when_enforcement_disabled(self):
        zone = DNSZone(
            name="a" * 64, filename="a" * 64 + ".zone", soa_mname="ns1." + "a" * 64 + ".", soa_rname="admin@example.com"
        )
        zone.full_clean()  # Should not raise

    def test_rejects_label_exceeding_63_bytes_when_enforcement_enabled(self):
        zone = DNSZone(
            name="a" * 64, filename="a" * 64 + ".zone", soa_mname="ns1." + "a" * 64 + ".", soa_rname="admin@example.com"
        )
        with self.assertRaises(ValidationError) as context:
            zone.full_clean()
        self.assertIn(
            "Label 'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa' exceeds the maximum length of 63 bytes (octets) in wire format",
            str(context.exception),
        )

    # Structure/Format Tests
    def test_rejects_empty_label(self):
        zone = DNSZone(
            name="example..com",
            filename="example..com.zone",
            soa_mname="ns1.example..com.",
            soa_rname="admin@example.com",
        )
        with self.assertRaises(ValidationError) as context:
            zone.full_clean()
        self.assertIn("Empty labels are not allowed", str(context.exception))

    def test_rejects_label_with_leading_or_trailing_dot(self):
        # Leading dot
        zone = DNSZone(
            name=".example",
            filename=".example.zone",
            soa_mname="ns1..example.",
            soa_rname="admin@example.com",
        )
        with self.assertRaises(ValidationError) as context:
            zone.full_clean()
        self.assertIn("Empty labels are not allowed", str(context.exception))
        # Trailing dot
        zone = DNSZone(
            name="example.",
            filename="example..zone",
            soa_mname="ns1.example..",
            soa_rname="admin@example.com",
        )
        with self.assertRaises(ValidationError) as context:
            zone.full_clean()
        self.assertIn("Empty labels are not allowed", str(context.exception))


class AutoCreatePTRRecordTestCase(TestCase):
    """Test the per-zone auto_create_ptr flag for ARecord/AAAARecord."""

    @classmethod
    def setUpTestData(cls):
        cls.status = Status.objects.get(name="Active")
        cls.namespace = Namespace.objects.get(name="Global")
        Prefix.objects.create(prefix="10.0.0.0/24", namespace=cls.namespace, type="Pool", status=cls.status)
        cls.ipv4 = IPAddress.objects.create(address="10.0.0.1/32", namespace=cls.namespace, status=cls.status)
        cls.ipv4_other = IPAddress.objects.create(address="10.0.0.2/32", namespace=cls.namespace, status=cls.status)
        Prefix.objects.create(prefix="192.168.1.0/24", namespace=cls.namespace, type="Pool", status=cls.status)
        cls.ipv4_unmatched = IPAddress.objects.create(
            address="192.168.1.1/32", namespace=cls.namespace, status=cls.status
        )
        Prefix.objects.create(prefix="2001:db8::/32", namespace=cls.namespace, type="Pool", status=cls.status)
        cls.ipv6 = IPAddress.objects.create(address="2001:db8::1/128", namespace=cls.namespace, status=cls.status)

        cls.view = DNSView.objects.create(name="View Default")
        cls.other_view = DNSView.objects.create(name="View Other")
        cls.fwd_off = DNSZone.objects.create(name="example.com", dns_view=cls.view, auto_create_ptr=False)
        cls.fwd_on = DNSZone.objects.create(name="auto.example.com", dns_view=cls.view, auto_create_ptr=True)
        cls.reverse_zone = DNSZone.objects.create(name="0.0.10.in-addr.arpa", dns_view=cls.view)

    def test_no_auto_ptr_when_flag_disabled(self):
        """auto_create_ptr=False: no PTR is created even if a matching reverse zone exists."""
        ARecord.objects.create(name="host1", ip_address=self.ipv4, zone=self.fwd_off)
        self.assertFalse(PTRRecord.objects.exists())

    def test_auto_ptr_creates_record_when_enabled(self):
        """auto_create_ptr=True with matching reverse zone in same view creates a PTR."""
        ARecord.objects.create(name="host1", ip_address=self.ipv4, zone=self.fwd_on)
        ptr = PTRRecord.objects.get(zone=self.reverse_zone, name="1")
        self.assertEqual(ptr.ptrdname, "host1.auto.example.com")

    def test_auto_ptr_raises_when_no_reverse_zone(self):
        """No matching reverse zone in same view raises ValidationError pre-insert; A record is not persisted."""
        with self.assertRaises(ValidationError):
            ARecord.objects.create(name="host2", ip_address=self.ipv4_unmatched, zone=self.fwd_on)
        self.assertFalse(ARecord.objects.filter(name="host2").exists())
        self.assertFalse(PTRRecord.objects.exists())

    def test_auto_ptr_does_not_use_reverse_zone_in_different_view(self):
        """A reverse zone in a different DNS view is NOT used; raises ValidationError."""
        DNSZone.objects.create(name="1.168.192.in-addr.arpa", dns_view=self.other_view)
        with self.assertRaises(ValidationError):
            ARecord.objects.create(name="host3", ip_address=self.ipv4_unmatched, zone=self.fwd_on)
        self.assertFalse(ARecord.objects.filter(name="host3").exists())
        self.assertFalse(PTRRecord.objects.exists())

    def test_auto_ptr_idempotent_when_ptr_already_exists(self):
        """If a PTR with the same owner name already exists in the reverse zone, no duplicate is created."""
        existing = PTRRecord.objects.create(name="1", ptrdname="host1.auto.example.com", zone=self.reverse_zone)
        ARecord.objects.create(name="host1", ip_address=self.ipv4, zone=self.fwd_on)
        ptrs = PTRRecord.objects.filter(name="1", zone=self.reverse_zone)
        self.assertEqual(ptrs.count(), 1)
        self.assertEqual(ptrs.first().pk, existing.pk)

    def test_auto_ptr_for_aaaa_record(self):
        """AAAARecord triggers PTR creation similarly when flag is on."""
        full_reverse = ipaddress_address("2001:db8::1", "reverse_pointer")
        parent_zone_name = ".".join(full_reverse.split(".")[1:])
        reverse_v6 = DNSZone.objects.create(name=parent_zone_name, dns_view=self.view)
        AAAARecord.objects.create(name="v6host", ip_address=self.ipv6, zone=self.fwd_on)
        ptr = PTRRecord.objects.get(zone=reverse_v6, name="1")
        self.assertEqual(ptr.ptrdname, "v6host.auto.example.com")


class TestDNSZoneFindForPtrdname(TestCase):
    """Test DNSZone.find_for_ptrdname classmethod."""

    @classmethod
    def setUpTestData(cls):
        cls.view_a = DNSView.objects.create(name="View A")
        cls.view_b = DNSView.objects.create(name="View B")

    def test_finds_most_specific_match(self):
        specific = DNSZone.objects.create(name="0.0.10.in-addr.arpa", dns_view=self.view_a)
        DNSZone.objects.create(name="10.in-addr.arpa", dns_view=self.view_a)
        self.assertEqual(DNSZone.find_reverse_zone_for_ptrdname("1.0.0.10.in-addr.arpa"), specific)

    def test_falls_back_to_less_specific_match(self):
        broad = DNSZone.objects.create(name="10.in-addr.arpa", dns_view=self.view_a)
        self.assertEqual(DNSZone.find_reverse_zone_for_ptrdname("1.0.0.10.in-addr.arpa"), broad)

    def test_returns_none_when_nothing_matches(self):
        self.assertIsNone(DNSZone.find_reverse_zone_for_ptrdname("1.2.3.4.in-addr.arpa"))

    def test_dns_view_scoping(self):
        """When dns_view is provided, only zones in that view are considered."""
        specific = DNSZone.objects.create(name="0.0.10.in-addr.arpa", dns_view=self.view_a)
        self.assertIsNone(DNSZone.find_reverse_zone_for_ptrdname("1.0.0.10.in-addr.arpa", dns_view=self.view_b))
        self.assertEqual(
            DNSZone.find_reverse_zone_for_ptrdname("1.0.0.10.in-addr.arpa", dns_view=self.view_a),
            specific,
        )


class DNSZoneIntegerFieldBoundaryTest(TestCase):
    """Boundary tests for integer fields on DNSZone.

    TTL (RFC 8767 §4): unsigned 32-bit, 0..4294967295.
    SOA fields (RFC 1035 §3.3.13): 32-bit values, explicitly unsigned for SERIAL and MINIMUM.
    RFC 1982 §7 governs SERIAL's uint32 range and arithmetic.
    """

    _INTEGER_FIELDS = ("ttl", "soa_refresh", "soa_retry", "soa_expire", "soa_serial", "soa_minimum")

    def _make_zone(self, **kwargs):
        defaults = {
            "name": "boundary-test.example",
            "filename": "boundary-test.zone",
            "soa_mname": "ns1.boundary-test.example.",
            "soa_rname": "admin@boundary-test.example",
            "ttl": 3600,
            "soa_refresh": 86400,
            "soa_retry": 7200,
            "soa_expire": 3600000,
            "soa_serial": 0,
            "soa_minimum": 3600,
        }
        defaults.update(kwargs)
        return DNSZone(**defaults)

    def test_all_fields_accept_zero(self):
        """All DNS integer zone fields accept 0 as a valid value."""
        for field in self._INTEGER_FIELDS:
            with self.subTest(field=field):
                zone = self._make_zone(name=f"{field}-zero.example", **{field: 0})
                zone.full_clean()

    def test_all_fields_accept_uint32_max(self):
        """All DNS integer zone fields accept the uint32 maximum."""
        for field in self._INTEGER_FIELDS:
            with self.subTest(field=field):
                zone = self._make_zone(name=f"{field}-max.example", **{field: UINT32_MAX})
                zone.full_clean()

    def test_all_fields_reject_above_uint32_max(self):
        """All DNS integer zone fields reject values above the uint32 maximum."""
        for field in self._INTEGER_FIELDS:
            with self.subTest(field=field):
                zone = self._make_zone(name=f"{field}-overflow.example", **{field: UINT32_MAX + 1})
                with self.assertRaises(ValidationError):
                    zone.full_clean()


class DNSRecordTTLBoundaryTest(TestCase):
    """Boundary tests for the record-level TTL field (RFC 8767 §4: unsigned 32-bit, 0..4294967295)."""

    @classmethod
    def setUpTestData(cls):
        cls.zone = DNSZone.objects.create(name="ttl-boundary.example", ttl=3600)

    def test_record_ttl_accepts_zero(self):
        """Record TTL of 0 is valid."""
        record = NSRecord(name="ns1", server="ns1.example.com.", zone=self.zone, _ttl=0)
        record.full_clean()

    def test_record_ttl_zero_not_replaced_by_zone_ttl(self):
        """TTL of 0 must not be treated as unset and silently replaced by the zone TTL (guards against falsy-check regression)."""
        record = NSRecord.objects.create(name="ns-zero", server="ns1.example.com.", zone=self.zone, _ttl=0)
        record.refresh_from_db()
        self.assertEqual(record.ttl, 0)

    def test_record_ttl_accepts_uint32_max(self):
        """Record TTL at the uint32 maximum is accepted."""
        record = NSRecord(name="ns1", server="ns1.example.com.", zone=self.zone, _ttl=UINT32_MAX)
        record.full_clean()

    def test_record_ttl_rejects_above_uint32_max(self):
        """Record TTL above the uint32 maximum is rejected."""
        record = NSRecord(name="ns1", server="ns1.example.com.", zone=self.zone, _ttl=UINT32_MAX + 1)
        with self.assertRaises(ValidationError):
            record.full_clean()

    def test_record_inherits_zone_ttl_when_no_record_ttl_set(self):
        """When no record-level TTL is set, the zone TTL is returned by the ttl property."""
        record = NSRecord.objects.create(name="ns1", server="ns1.example.com.", zone=self.zone)
        self.assertEqual(record.ttl, self.zone.ttl)


class DNSModelEnabledFieldTest(TestCase):
    """Tests for the `enabled` field that DNSZone and every record type inherit from DNSModel."""

    @classmethod
    def setUpTestData(cls):
        # Populate the required zone fields so the zone can be re-saved with validated_save().
        cls.zone = DNSZone.objects.create(
            name="enabled.example",
            filename="enabled.example.zone",
            soa_mname="ns1.enabled.example",
            soa_rname="admin@enabled.example",
        )
        status = Status.objects.get(name="Active")
        namespace = Namespace.objects.get(name="Global")
        Prefix.objects.create(prefix="10.10.0.0/24", namespace=namespace, type="Pool", status=status)
        cls.ip_address = IPAddress.objects.create(address="10.10.0.1/32", namespace=namespace, status=status)
        Prefix.objects.create(prefix="2001:db8:abcd:77::/64", namespace=namespace, type="Pool", status=status)
        cls.ipv6_address = IPAddress.objects.create(
            address="2001:db8:abcd:77::1/128", namespace=namespace, status=status
        )

    def _records(self, suffix, **kwargs):
        """Return one unsaved record of every type, all named after `suffix`."""
        return [
            NSRecord(name=f"ns-{suffix}", server="ns1.example.com.", zone=self.zone, **kwargs),
            ARecord(name=f"a-{suffix}", ip_address=self.ip_address, zone=self.zone, **kwargs),
            AAAARecord(name=f"aaaa-{suffix}", ip_address=self.ipv6_address, zone=self.zone, **kwargs),
            CNAMERecord(name=f"cname-{suffix}", alias="www.example.com", zone=self.zone, **kwargs),
            MXRecord(name=f"mx-{suffix}", mail_server="mail.example.com", zone=self.zone, **kwargs),
            TXTRecord(name=f"txt-{suffix}", text="v=spf1 -all", zone=self.zone, **kwargs),
            PTRRecord(name=f"ptr-{suffix}", ptrdname="www.example.com", zone=self.zone, **kwargs),
            SRVRecord(
                name=f"srv-{suffix}",
                priority=10,
                weight=5,
                port=5060,
                target="sip.example.com",
                zone=self.zone,
                **kwargs,
            ),
        ]

    def test_zone_is_enabled_by_default(self):
        """A zone is eligible for publication unless explicitly disabled."""
        self.assertTrue(DNSZone.objects.create(name="default.example").enabled)

    def test_zone_can_be_disabled(self):
        """A zone's enabled flag can be set to False."""
        zone = DNSZone.objects.create(name="disabled.example", enabled=False)
        zone.refresh_from_db()
        self.assertFalse(zone.enabled)

    def test_records_are_enabled_by_default(self):
        """Every record type inherits enabled=True from DNSModel."""
        for record in self._records("default"):
            with self.subTest(model=type(record).__name__):
                record.validated_save()
                record.refresh_from_db()
                self.assertTrue(record.enabled)

    def test_records_can_be_disabled(self):
        """Every record type can be created with enabled=False."""
        for record in self._records("disabled", enabled=False):
            with self.subTest(model=type(record).__name__):
                record.validated_save()
                record.refresh_from_db()
                self.assertFalse(record.enabled)

    def test_disabling_zone_does_not_disable_its_records(self):
        """The zone and record flags are independent; this app does not cascade them."""
        record = NSRecord.objects.create(name="ns-cascade", server="ns1.example.com.", zone=self.zone)

        self.zone.enabled = False
        self.zone.validated_save()

        record.refresh_from_db()
        self.assertTrue(record.enabled)


def _zone(name, dns_view=None):
    """Create a zone with validated_save(), so parent_zone is computed the way the UI and API compute it."""
    zone = DNSZone(name=name, filename=f"{name}.zone", soa_mname=f"ns1.{name}", soa_rname=f"admin@{name}")
    if dns_view is not None:
        zone.dns_view = dns_view
    zone.validated_save()
    return zone


def _ip(address):
    """Create an IP address in the Global namespace, creating its parent prefix if needed."""
    namespace = Namespace.objects.get(name="Global")
    active = Status.objects.get(name="Active")
    prefix = "10.0.0.0/8" if ":" not in address else "2001:db8::/32"
    Prefix.objects.get_or_create(prefix=prefix, namespace=namespace, defaults={"status": active})
    return IPAddress.objects.create(address=address, namespace=namespace, status=active)


class DNSZoneHierarchyTestCase(TestCase):
    """Test that DNSZone.parent_zone always points to the nearest existing ancestor zone in the same view."""

    def assertParent(self, zone, expected_parent):  # pylint: disable=invalid-name
        """Assert the zone's stored parent_zone, as read back from the database."""
        zone.refresh_from_db()
        self.assertEqual(zone.parent_zone, expected_parent)

    def test_parent_zone_is_nearest_existing_ancestor(self):
        example = _zone("example.com")
        deep = _zone("a.b.example.com")
        unrelated = _zone("example.org")

        self.assertParent(example, None)
        self.assertParent(deep, example)
        self.assertParent(unrelated, None)

    def test_creating_zone_moves_descendants_under_it(self):
        example = _zone("example.com")
        deep = _zone("a.b.example.com")
        sibling = _zone("c.example.com")

        middle = _zone("b.example.com")

        self.assertParent(middle, example)
        self.assertParent(deep, middle)
        self.assertParent(sibling, example)

    def test_deleting_zone_moves_children_to_grandparent(self):
        example = _zone("example.com")
        middle = _zone("b.example.com")
        deep = _zone("a.b.example.com")

        middle.delete()

        self.assertParent(deep, example)

    def test_bulk_deleting_zones_moves_children_to_nearest_remaining_ancestor(self):
        example = _zone("example.com")
        _zone("b.example.com")
        _zone("c.b.example.com")
        deepest = _zone("d.c.b.example.com")

        DNSZone.objects.filter(name__in=["b.example.com", "c.b.example.com"]).delete()

        self.assertParent(deepest, example)

    def test_deleting_root_zone_leaves_children_without_parent(self):
        example = _zone("example.com")
        child = _zone("a.example.com")

        example.delete()

        self.assertParent(child, None)

    def test_renaming_zone_updates_old_and_new_children(self):
        example = _zone("example.com")
        renamed = _zone("x.example.com")
        old_child = _zone("a.x.example.com")
        new_child = _zone("a.y.example.com")

        renamed.name = "y.example.com"
        renamed.validated_save()

        self.assertParent(old_child, example)
        self.assertParent(new_child, renamed)

    def test_parent_zone_is_scoped_to_dns_view(self):
        other_view = DNSView.objects.create(name="Other")
        example = _zone("example.com")
        child = _zone("sub.example.com", dns_view=other_view)
        self.assertParent(child, None)

        child.dns_view = example.dns_view
        child.validated_save()

        self.assertParent(child, example)

    def test_parent_zone_matching_ignores_case(self):
        example = _zone("Example.COM")
        child = _zone("sub.example.com")

        self.assertParent(child, example)

    def test_data_migration_populates_parent_zone_for_existing_zones(self):
        example = _zone("example.com")
        child = _zone("a.b.example.com")
        other_view_child = _zone("c.example.com", dns_view=DNSView.objects.create(name="Other"))
        DNSZone.objects.update(parent_zone=None)

        migration = importlib.import_module("nautobot_dns_models.migrations.0012_populate_dnszone_parent_zone")
        migration.populate_parent_zone(django_apps, None)

        self.assertParent(child, example)
        self.assertParent(other_view_child, None)


class DNSZoneDelegationTestCase(TestCase):
    """Test how delegations are derived from NS records and how their consistency is checked."""

    @classmethod
    def setUpTestData(cls):
        cls.parent = _zone("example.com")
        NSRecord.objects.create(zone=cls.parent, name="@", server="ns1.example.com")

    def _delegate(self, name, *servers):
        for server in servers:
            NSRecord.objects.create(zone=self.parent, name=name, server=server)

    def _delegation(self, fqdn):
        return next(delegation for delegation in self.parent.get_delegations() if delegation.fqdn == fqdn)

    def test_apex_ns_records_are_not_delegations(self):
        NSRecord.objects.create(zone=self.parent, name="example.com", server="ns2.example.com")

        self.assertEqual(self.parent.get_delegations(), [])
        self.assertEqual(self.parent.get_apex_ns_servers(), ["ns1.example.com", "ns2.example.com"])

    def test_internal_delegation_links_child_zone_and_glue(self):
        child = _zone("apps.example.com")
        self._delegate("apps", "ns1.apps.example.com", "ns2.apps.example.com")
        glue = ARecord.objects.create(zone=self.parent, name="ns1.apps", ip_address=_ip("10.0.0.1/32"))

        delegation = self._delegation("apps.example.com")

        self.assertEqual(delegation.child_zone, child)
        self.assertEqual(delegation.servers, ["ns1.apps.example.com", "ns2.apps.example.com"])
        self.assertEqual(delegation.glue_records, [glue])
        self.assertEqual(delegation.missing_glue_servers, ["ns2.apps.example.com"])

    def test_external_delegation_has_no_child_zone_and_needs_no_glue(self):
        self._delegate("mail", "ns1.mailvendor.net", "ns2.mailvendor.net")

        delegation = self._delegation("mail.example.com")

        self.assertIsNone(delegation.child_zone)
        self.assertEqual(delegation.glue_required_servers, [])
        self.assertEqual(self.parent.get_delegation_warnings(), [])

    def test_zone_qualified_ns_record_name_is_recognized(self):
        self._delegate("mail.example.com", "ns1.mailvendor.net")

        self.assertEqual([delegation.fqdn for delegation in self.parent.get_delegations()], ["mail.example.com"])

    def test_ns_records_below_a_delegation_are_occluded_not_delegated(self):
        self._delegate("mail", "ns1.mailvendor.net")
        self._delegate("eu.mail", "ns1.eu.mailvendor.net")

        self.assertEqual([delegation.fqdn for delegation in self.parent.get_delegations()], ["mail.example.com"])
        self.assertEqual([record.name for record in self.parent.get_occluded_records()], ["eu.mail"])

    def test_records_below_a_delegation_are_occluded_except_glue(self):
        self._delegate("apps", "ns1.apps.example.com")
        self._delegate("mail", "ns1.mail.example.com")
        ARecord.objects.create(zone=self.parent, name="ns1.apps", ip_address=_ip("10.0.0.1/32"))
        ARecord.objects.create(zone=self.parent, name="ns1.mail", ip_address=_ip("10.0.0.2/32"))
        hidden = TXTRecord.objects.create(zone=self.parent, name="legacy.mail", text="hidden")
        at_cut = CNAMERecord.objects.create(zone=self.parent, name="apps", alias="www.example.com")
        TXTRecord.objects.create(zone=self.parent, name="www", text="served")

        occluded = self.parent.get_occluded_records()

        self.assertCountEqual(occluded, [hidden, at_cut])
        self.assertIn("2 record(s) at or below a delegation point", " ".join(self.parent.get_delegation_warnings()))

    def test_sibling_glue_is_not_occluded(self):
        self._delegate("apps", "ns1.mail.example.com")
        self._delegate("mail", "ns1.mail.example.com")
        ARecord.objects.create(zone=self.parent, name="ns1.mail", ip_address=_ip("10.0.0.2/32"))

        self.assertEqual(self.parent.get_occluded_records(), [])

    def test_missing_glue_is_reported(self):
        self._delegate("mail", "ns1.mail.example.com")

        warnings = self.parent.get_delegation_warnings()

        self.assertEqual(len(warnings), 1)
        self.assertIn("ns1.mail.example.com is inside the delegated name but has no A/AAAA glue", warnings[0])

    def test_name_server_mismatch_is_reported_on_both_sides(self):
        child = _zone("apps.example.com")
        NSRecord.objects.create(zone=child, name="@", server="ns1.other.net")
        self._delegate("apps", "ns1.provider.net")

        parent_warnings = self.parent.get_delegation_warnings()
        child_warnings = child.get_delegation_warnings()

        self.assertEqual(len(parent_warnings), 1)
        self.assertIn("do not match the apex NS records of zone apps.example.com", parent_warnings[0])
        self.assertEqual(len(child_warnings), 1)
        self.assertIn("parent zone example.com (ns1.provider.net) do not match", child_warnings[0])

    def test_child_zone_without_delegation_is_reported_on_both_sides(self):
        child = _zone("lab.example.com")

        self.assertEqual(
            self.parent.get_delegation_warnings(),
            ["Child zone lab.example.com has no NS records in this zone, so it is not delegated."],
        )
        self.assertEqual(
            child.get_delegation_warnings(),
            ["Parent zone example.com has no NS records for this zone, so it is not delegated."],
        )
        self.assertIsNone(child.get_parent_delegation())

    def test_zone_qualified_records_below_a_delegation_are_occluded(self):
        self._delegate("mail", "ns1.mailvendor.net")
        hidden = TXTRecord.objects.create(zone=self.parent, name="legacy.mail.example.com", text="hidden")

        self.assertEqual(self.parent.get_occluded_records(), [hidden])

    def test_query_count_does_not_grow_with_delegations_or_records(self):
        def count_queries():
            with CaptureQueriesContext(connection) as context:
                delegations = self.parent.get_delegations()
                self.parent.get_delegation_warnings(delegations)
            return len(context.captured_queries)

        def add_internal_delegation(label):
            child = _zone(f"{label}.example.com")
            NSRecord.objects.create(zone=child, name="@", server="ns1.provider.net")
            self._delegate(label, "ns1.provider.net")

        add_internal_delegation("one")
        baseline = count_queries()
        for label in ("two", "three", "four"):
            add_internal_delegation(label)
            TXTRecord.objects.create(zone=self.parent, name=f"txt.{label}", text="hidden")

        self.assertEqual(count_queries(), baseline)

    def test_zone_below_another_delegation_is_not_reported_as_undelegated(self):
        self._delegate("a", "ns1.provider.net")
        grandchild = _zone("b.a.example.com")

        self.assertEqual(grandchild.parent_zone, self.parent)
        self.assertEqual(self.parent.get_delegation_warnings(), [])
        self.assertEqual(grandchild.get_delegation_warnings(), [])

    def test_consistent_internal_delegation_has_no_warnings(self):
        child = _zone("apps.example.com")
        NSRecord.objects.create(zone=child, name="@", server="ns1.apps.example.com")
        self._delegate("apps", "NS1.Apps.Example.com.")
        ARecord.objects.create(zone=self.parent, name="ns1.apps", ip_address=_ip("10.0.0.1/32"))

        self.assertEqual(self.parent.get_delegation_warnings(), [])
        self.assertEqual(child.get_delegation_warnings(), [])
        self.assertEqual(child.get_parent_delegation().fqdn, "apps.example.com")

    def test_delegations_do_not_cross_dns_views(self):
        _zone("apps.example.com", dns_view=DNSView.objects.create(name="Other"))
        self._delegate("apps", "ns1.provider.net")

        self.assertIsNone(self._delegation("apps.example.com").child_zone)


class TestDNSForwardingRule(ModelTestCases.BaseModelTestCase):
    """Generic model tests for DNSForwardingRule."""

    model = DNSForwardingRule

    @classmethod
    def setUpTestData(cls):
        DNSForwardingRule.objects.create(name="corp.example.com")
        DNSForwardingRule.objects.create(name="partner.example.net")
        DNSForwardingRule.objects.create(name=".")


class _DNSForwardingRuleTestBase(TestCase):
    """Shared fixtures and helpers for the DNSForwardingRule test cases."""

    @classmethod
    def setUpTestData(cls):
        cls.view = DNSView.objects.get(name="Default")
        cls.other_view = DNSView.objects.create(name="Internal")
        cls.forwarder = _ip("10.0.0.53/32")

    def _rule(self, name, **kwargs):
        rule = DNSForwardingRule(name=name, **kwargs)
        rule.validated_save()
        return rule

    def _forward(self, rule, ip_address=None, **kwargs):
        assignment = DNSForwardingRuleIPAddressAssignment(
            forwarding_rule=rule, ip_address=ip_address or self.forwarder, **kwargs
        )
        assignment.validated_save()
        return assignment


class DNSForwardingRuleValidationTestCase(_DNSForwardingRuleTestBase):
    """Test DNSForwardingRule and DNSForwardingRuleIPAddressAssignment validation."""

    def test_defaults(self):
        rule = self._rule("corp.example.com")

        self.assertEqual(rule.dns_view, self.view)
        self.assertEqual(rule.action, DNSForwardingRuleActionChoices.ACTION_FORWARD_FIRST)
        self.assertTrue(rule.enabled)
        self.assertEqual(str(rule), "corp.example.com (Default)")
        self.assertEqual(rule.get_action_class(), "info")

    def test_single_dot_is_the_global_rule(self):
        rule = self._rule(".")

        self.assertTrue(rule.is_global)

    def test_name_labels_are_validated(self):
        with self.assertRaises(ValidationError) as context:
            self._rule("bad..example.com")
        self.assertIn("Empty labels are not allowed", str(context.exception))

    @override_config(nautobot_dns_models__DNS_VALIDATION_LEVEL="none")
    def test_name_labels_are_not_validated_when_validation_is_disabled(self):
        self._rule("bad..example.com")

    def test_name_is_unique_per_view(self):
        self._rule("corp.example.com")
        self._rule("corp.example.com", dns_view=self.other_view)

        with self.assertRaises(ValidationError):
            self._rule("corp.example.com")

    def test_name_is_unique_per_view_regardless_of_case(self):
        self._rule("corp.example.com")

        with self.assertRaises(ValidationError) as context:
            self._rule("Corp.Example.com")
        self.assertIn("A DNS forwarding rule with this name already exists", str(context.exception))

    def test_rule_cannot_reuse_a_zone_name_in_the_same_view(self):
        _zone("corp.example.com")

        with self.assertRaises(ValidationError) as context:
            self._rule("CORP.example.com")
        self.assertIn("A DNS zone with this name exists in this view", str(context.exception))
        self._rule("corp.example.com", dns_view=self.other_view)

    def test_zone_cannot_reuse_a_rule_name_in_the_same_view(self):
        self._rule("corp.example.com")

        with self.assertRaises(ValidationError) as context:
            _zone("corp.example.com")
        self.assertIn("A DNS forwarding rule with this name already exists", str(context.exception))
        _zone("corp.example.com", dns_view=self.other_view)

    def test_do_not_forward_rule_rejects_forwarders(self):
        rule = self._rule("public.example.net", action=DNSForwardingRuleActionChoices.ACTION_DO_NOT_FORWARD)

        with self.assertRaises(ValidationError) as context:
            self._forward(rule)
        self.assertIn("cannot have forwarders", str(context.exception))

    def test_rule_with_forwarders_cannot_switch_to_do_not_forward(self):
        rule = self._rule("corp.example.com")
        self._forward(rule)

        rule.action = DNSForwardingRuleActionChoices.ACTION_DO_NOT_FORWARD
        with self.assertRaises(ValidationError) as context:
            rule.validated_save()
        self.assertIn("Remove this rule's forwarders", str(context.exception))

    def test_forwarder_is_unique_per_rule_address_and_port(self):
        rule = self._rule("corp.example.com")
        self._forward(rule, port=53)
        self._forward(rule, port=5353)

        with self.assertRaises(ValidationError):
            self._forward(rule, port=53)

    def test_forwarder_port_must_be_a_valid_port(self):
        rule = self._rule("corp.example.com")
        for port in (0, 65536):
            with self.subTest(port=port), self.assertRaises(ValidationError):
                self._forward(rule, port=port)

    def test_forwarders_are_ordered_by_weight(self):
        rule = self._rule("corp.example.com")
        second = self._forward(rule, ip_address=_ip("10.0.0.54/32"), weight=20)
        first = self._forward(rule, weight=10)

        self.assertEqual(list(rule.forwarder_assignments.all()), [first, second])
        self.assertCountEqual(rule.forwarders.all(), [first.ip_address, second.ip_address])
        self.assertEqual(list(self.forwarder.dns_forwarding_rules.all()), [rule])

    def test_deleting_rule_or_ip_address_deletes_its_forwarder_assignments(self):
        rule = self._rule("corp.example.com")
        other_ip = _ip("10.0.0.54/32")
        self._forward(rule)
        self._forward(rule, ip_address=other_ip)

        other_ip.delete()
        self.assertEqual(rule.forwarder_assignments.count(), 1)
        rule.delete()
        self.assertFalse(DNSForwardingRuleIPAddressAssignment.objects.exists())


class DNSForwardingRuleWarningsTestCase(_DNSForwardingRuleTestBase):
    """Test the warnings DNSForwardingRule reports for rules that cannot work as intended."""

    def test_warning_when_forwarding_rule_has_no_forwarders(self):
        rule = self._rule("corp.example.com")

        self.assertEqual(rule.get_warnings(), ["No forwarders are assigned, so this rule has nowhere to send queries."])

    def test_do_not_forward_rule_has_no_warnings(self):
        _zone("example.com")
        rule = self._rule("corp.example.com", action=DNSForwardingRuleActionChoices.ACTION_DO_NOT_FORWARD)

        self.assertEqual(rule.get_warnings(), [])

    def test_warning_when_rule_is_inside_a_zone_without_delegation(self):
        _zone("example.com")
        rule = self._rule("corp.example.com")
        self._forward(rule)

        warnings = rule.get_warnings()

        self.assertEqual(len(warnings), 1)
        self.assertIn("is inside zone example.com in the same view", warnings[0])

    def test_no_warning_when_rule_is_inside_a_delegated_name(self):
        zone = _zone("example.com")
        NSRecord.objects.create(zone=zone, name="corp", server="dc1.corp.example.com")
        rule = self._rule("east.corp.example.com")
        self._forward(rule)

        self.assertEqual(rule.get_warnings(), [])

    def test_no_warning_for_zones_in_other_views(self):
        _zone("example.com", dns_view=self.other_view)
        rule = self._rule("corp.example.com")
        self._forward(rule)

        self.assertEqual(rule.get_warnings(), [])

    def test_global_rule_is_never_inside_a_zone(self):
        _zone("example.com")
        rule = self._rule(".")
        self._forward(rule)

        self.assertEqual(rule.get_warnings(), [])
