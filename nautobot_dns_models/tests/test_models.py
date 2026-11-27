"""Test DNSZone."""
# pylint: disable=too-many-lines

import itertools
from io import StringIO

from constance.test import override_config
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from django.core.management import call_command
from django.db import IntegrityError, connection, transaction
from django.db.models import ProtectedError, QuerySet
from django.test.utils import CaptureQueriesContext
from nautobot.apps.change_logging import web_request_context
from nautobot.apps.testing import ModelTestCases, TestCase
from nautobot.extras.models import ObjectChange, Status
from nautobot.ipam.models import IPAddress, Namespace, Prefix
from netutils.ip import ipaddress_address

from nautobot_dns_models.choices import DNSZoneTypeChoices, NameServerRelationshipChoices
from nautobot_dns_models.models import (
    APEX_RECORD_NAME,
    CATALOG_APEX_NS_SERVER,
    TXT_CHARACTER_STRING_MAX_OCTETS,
    TXT_RDATA_MAX_OCTETS,
    UINT32_MAX,
    AAAARecord,
    ARecord,
    CNAMERecord,
    DNSDelegation,
    DNSForwarder,
    DNSForwardingRule,
    DNSRegistrar,
    DNSRegistration,
    DNSView,
    DNSViewPrefixAssignment,
    DNSZone,
    MXRecord,
    NSRecord,
    PTRRecord,
    SRVRecord,
    TXTRecord,
    catalog_member_label,
    dns_wire_label_length,
    get_address_records,
    rebuild_zone_hierarchy,
    split_txt_character_strings,
    txt_wire_rdata_length,
)
from nautobot_dns_models.querysets import dns_record_models
from nautobot_dns_models.system_writes import system_write
from nautobot_dns_models.tests.fixtures import create_zone


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
        DNSRegistrar.objects.create(
            name="Registrar 1", portal_url="https://registrar1.example", account_number="ACC-001"
        )
        DNSRegistrar.objects.create(
            name="Registrar 2", portal_url="https://registrar2.example", account_number="ACC-002"
        )
        DNSRegistrar.objects.create(
            name="Registrar 3", portal_url="https://registrar3.example", account_number="ACC-003"
        )

    def test_create_dnsregistrar_only_required(self):
        """Create with only required fields."""
        registrar = DNSRegistrar.objects.create(name="Test Registrar")
        self.assertEqual(registrar.name, "Test Registrar")
        self.assertEqual(registrar.portal_url, "")
        self.assertEqual(registrar.account_number, "")
        self.assertEqual(str(registrar), "Test Registrar")

    def test_create_dnsregistrar_all_fields_success(self):
        """Create DNSRegistrar with all fields."""
        registrar = DNSRegistrar.objects.create(
            name="Another Registrar",
            portal_url="https://another-registrar.example",
            account_number="ACCT-1234",
        )
        self.assertEqual(registrar.name, "Another Registrar")
        self.assertEqual(registrar.portal_url, "https://another-registrar.example")
        self.assertEqual(registrar.account_number, "ACCT-1234")

    def test_get_absolute_url(self):
        registrar = DNSRegistrar.objects.get(name="Registrar 1")
        self.assertEqual(registrar.get_absolute_url(), f"/plugins/dns/dns-registrars/{registrar.id}/")


class TestDNSRegistration(ModelTestCases.BaseModelTestCase):
    """Test DNSRegistration model."""

    model = DNSRegistration

    @classmethod
    def setUpTestData(cls):
        """Create test data for DNSRegistration Model."""
        super().setUpTestData()
        for i in range(3):
            DNSZone.objects.create(name=f"Test Zone {i}", type=DNSZoneTypeChoices.TYPE_PRIMARY)

        cls.registrar = DNSRegistrar.objects.create(name="Test Registrar")
        status = Status.objects.get(name="Active")
        status.content_types.add(ContentType.objects.get_for_model(DNSRegistration))
        cls.status = status

        DNSRegistration.objects.create(
            dns_registrar=cls.registrar,
            status=cls.status,
            dns_zone=DNSZone.objects.get(name="Test Zone 0"),
        )

    def test_registration_accepts_primary_zone(self):
        """Registration accepts a primary zone."""
        primary_zone = DNSZone.objects.create(name="Test Primary", type=DNSZoneTypeChoices.TYPE_PRIMARY)
        registration = DNSRegistration(
            dns_registrar=self.registrar,
            status=self.status,
            dns_zone=primary_zone,
        )
        registration.validated_save()

        self.assertEqual(registration.dns_zone, primary_zone)

    def test_registration_rejects_catalog_zone(self):
        """Registration rejects a catalog zone."""
        catalog_zone = DNSZone.objects.create(name="Test Catalog", type=DNSZoneTypeChoices.TYPE_CATALOG)
        with self.assertRaises(ValidationError) as context:
            DNSRegistration(
                dns_registrar=self.registrar,
                status=self.status,
                dns_zone=catalog_zone,
            ).validated_save()

        self.assertEqual(context.exception.message_dict["dns_zone"], ["Catalog zones cannot be registered."])


class TestDNSZone(ModelTestCases.BaseModelTestCase):
    """Test DNSZone model."""

    model = DNSZone

    @classmethod
    def setUpTestData(cls):
        """Create test data for DNSZone Model."""
        super().setUpTestData()
        # Create 3 objects for the model test cases.
        DNSZone.objects.create(name="Test One")
        DNSZone.objects.create(name="Test Two")
        DNSZone.objects.create(name="Test Three")

    @staticmethod
    def _make_zone(name, **kwargs):
        """Build an unsaved DNSZone populated with every field full_clean() requires."""
        defaults = {
            "name": name,
            "filename": f"{name}.zone",
            "soa_mname": f"ns1.{name}.",
            "soa_rname": f"admin@{name}",
        }
        defaults.update(kwargs)
        return DNSZone(**defaults)

    def test_create_dnszone_only_required(self):
        """Create with only required fields, and validate null description and __str__."""
        dnszone = DNSZone.objects.create(name="Development")
        self.assertEqual(dnszone.name, "Development")
        self.assertEqual(dnszone.description, "")
        self.assertTrue(dnszone.enabled)
        self.assertEqual(str(dnszone), "Development (Default)")

    def test_create_dnszone_all_fields_success(self):
        """Create DNSZone with all fields."""
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

    def test_name_preserves_entered_case(self):
        """The zone name is stored as entered."""
        dnszone = DNSZone.objects.create(name="Example.COM")
        dnszone.refresh_from_db()
        self.assertEqual(dnszone.name, "Example.COM")

    def test_name_case_variant_in_same_view_fails_validation(self):
        """A zone whose name differs from another zone in the same view only by case is rejected on `name`."""
        DNSZone.objects.create(name="example.com")
        dnszone = DNSZone(
            name="Example.COM",
            filename="example.com.zone",
            soa_mname="ns1.example.com",
            soa_rname="admin@example.com",
        )
        with self.assertRaises(ValidationError) as context:
            dnszone.full_clean()
        self.assertEqual(
            context.exception.message_dict,
            {"name": ["A DNS zone with this name (ignoring letter case) already exists in this view."]},
        )

    def test_name_case_variant_in_same_view_fails_in_database(self):
        """The database rejects a case variant even when model validation is bypassed."""
        DNSZone.objects.create(name="example.com")
        with self.assertRaises(IntegrityError), transaction.atomic():
            DNSZone.objects.create(name="EXAMPLE.com")

    def test_name_case_variant_in_other_view_succeeds(self):
        """The same name in a different case is allowed in a different view."""
        DNSZone.objects.create(name="example.com")
        other_view = DNSView.objects.create(name="Other View")
        dnszone = DNSZone(
            name="Example.com",
            dns_view=other_view,
            filename="example.com.zone",
            soa_mname="ns1.example.com",
            soa_rname="admin@example.com",
        )
        dnszone.full_clean()
        dnszone.save()
        self.assertEqual(DNSZone.objects.filter(name__iexact="example.com").count(), 2)

    def test_changing_case_of_own_name_succeeds(self):
        """A zone can change the case of its own name."""
        dnszone = DNSZone.objects.create(
            name="example.com",
            filename="example.com.zone",
            soa_mname="ns1.example.com",
            soa_rname="admin@example.com",
        )
        dnszone.name = "Example.com"
        dnszone.validated_save()
        dnszone.refresh_from_db()
        self.assertEqual(dnszone.name, "Example.com")

    def test_natural_key_field_lookups(self):
        """The natural key is unchanged by the switch to a case-insensitive constraint."""
        self.assertEqual(DNSZone.natural_key_field_lookups, ["name", "dns_view__name"])

    def test_default_zone_type_is_primary(self):
        """A zone created without an explicit type is a primary zone."""
        zone = DNSZone.objects.create(name="default-type.example")
        self.assertEqual(zone.type, DNSZoneTypeChoices.TYPE_PRIMARY)

    def test_rejects_zone_type_change(self):
        """Changing `type` on an existing zone is rejected."""
        zone = self._make_zone("immutable.example")
        zone.validated_save()
        zone.type = DNSZoneTypeChoices.TYPE_CATALOG

        with self.assertRaises(ValidationError) as context:
            zone.full_clean()

        self.assertEqual(
            context.exception.message_dict["type"][0],
            "Zone type cannot be changed after creation.",
        )

    def test_rejects_zone_type_change_on_bare_save(self):
        """A type change is refused on a bare save, which skips validation."""
        zone = self._make_zone("immutable-save.example")
        zone.validated_save()
        zone.type = DNSZoneTypeChoices.TYPE_CATALOG

        with self.assertRaises(ValidationError) as context:
            zone.save()

        self.assertEqual(
            context.exception.message_dict["type"][0],
            "Zone type cannot be changed after creation.",
        )

    def test_rejects_zone_type_change_through_a_queryset(self):
        """`update()` and `bulk_update()` refuse to change `type`, and store nothing."""
        zone = self._make_zone("immutable-queryset.example")
        zone.validated_save()
        zone.type = DNSZoneTypeChoices.TYPE_CATALOG

        test_cases = [
            ("update", lambda: DNSZone.objects.filter(pk=zone.pk).update(type=DNSZoneTypeChoices.TYPE_CATALOG)),
            ("bulk_update", lambda: DNSZone.objects.bulk_update([zone], ["type"])),
        ]

        for method, change_fn in test_cases:
            with self.subTest(method=method):
                with self.assertRaises(ValidationError) as context:
                    change_fn()

                self.assertEqual(
                    context.exception.message_dict["type"][0],
                    "Zone type cannot be changed after creation.",
                )
                self.assertEqual(DNSZone.objects.get(pk=zone.pk).type, DNSZoneTypeChoices.TYPE_PRIMARY)

    def test_rejected_zone_type_change_writes_no_catalog_records(self):
        """A refused type change writes none of a catalog zone's records."""
        zone = self._make_zone("immutable-records.example")
        zone.validated_save()
        zone.type = DNSZoneTypeChoices.TYPE_CATALOG
        with self.assertRaises(ValidationError):
            zone.save(update_fields={"description"})

        zone.refresh_from_db()
        self.assertEqual(zone.type, DNSZoneTypeChoices.TYPE_PRIMARY)
        self.assertFalse(NSRecord.objects.filter(zone=zone).exists())
        self.assertFalse(TXTRecord.objects.filter(zone=zone).exists())

    def test_primary_zone_allows_auto_create_ptr(self):
        """A primary zone accepts `auto_create_ptr`."""
        zone = self._make_zone("ptr-ok.example", auto_create_ptr=True)
        zone.validated_save()
        self.assertTrue(zone.auto_create_ptr)

    def test_catalog_zone_rejects_auto_create_ptr(self):
        """Validation rejects `auto_create_ptr` on a catalog zone rather than ignoring it."""
        zone = self._make_zone("catalog-ptr.example", type=DNSZoneTypeChoices.TYPE_CATALOG, auto_create_ptr=True)
        with self.assertRaises(ValidationError) as context:
            zone.full_clean()
        self.assertEqual(
            context.exception.message_dict["auto_create_ptr"][0],
            "Catalog zones cannot enable automatic PTR creation.",
        )

    def test_catalog_zone_auto_create_ptr_blocked_at_database(self):
        """The database refuses `auto_create_ptr` on a catalog zone when validation is skipped."""
        zone = DNSZone.objects.create(name="catalog-db.example", type=DNSZoneTypeChoices.TYPE_CATALOG)
        with self.assertRaises(IntegrityError):
            DNSZone.objects.filter(pk=zone.pk).update(auto_create_ptr=True)

    def test_is_a_single_dns_safe_label(self):
        """A generated member label is 26 characters from [a-z2-7], a single DNS-safe label.

        It is the unpadded lowercase base32 of a UUID, inside RFC 1035 §3.1.
        """
        label = catalog_member_label()
        self.assertEqual(len(label), 26)
        self.assertRegex(label, r"^[a-z2-7]+$")

    def test_primary_zone_with_records_is_protected(self):
        """Deleting a primary zone that has records is refused."""
        zone = create_zone("primary.example")
        record = NSRecord.objects.create(name="ns1", server="ns1.primary.example.", zone=zone)
        for path, delete_fn in (
            ("instance", zone.delete),
            ("queryset", DNSZone.objects.filter(pk=zone.pk).delete),
        ):
            with self.subTest(path=path):
                with self.assertRaises(ProtectedError):
                    delete_fn()
                self.assertTrue(NSRecord.objects.filter(pk=record.pk).exists())


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


class TXTRecordTextValidationTest(TestCase):
    """Test TXT record content validation rules from RFC 1035 §3.3.14."""

    @classmethod
    def setUpTestData(cls):
        cls.zone = DNSZone.objects.create(name="example.com")

    @staticmethod
    def _dkim_value(length):
        """Return a DKIM-shaped TXT value of exactly `length` characters."""
        prefix = "v=DKIM1; k=rsa; p="
        return prefix + "A" * (length - len(prefix))

    # Per-character-string length (RFC 1035 §3.3)
    def test_accepts_character_string_of_255_octets(self):
        record = TXTRecord(name="txt", text="a" * TXT_CHARACTER_STRING_MAX_OCTETS, zone=self.zone)
        record.full_clean()  # Should not raise

    def test_rejects_quoted_character_string_exceeding_255_octets(self):
        record = TXTRecord(name="txt", text='"' + "a" * 300 + '"', zone=self.zone)
        with self.assertRaises(ValidationError) as context:
            record.full_clean()
        self.assertIn("Character-string 1 is 300 bytes (octets) but the maximum is 255", str(context.exception))

    def test_reports_position_of_the_offending_character_string(self):
        record = TXTRecord(name="txt", text='"short" "' + "a" * 256 + '"', zone=self.zone)
        with self.assertRaises(ValidationError) as context:
            record.full_clean()
        self.assertIn("Character-string 2 is 256 bytes (octets)", str(context.exception))

    # Long plain values are chunked rather than rejected
    def test_accepts_text_longer_than_the_former_256_character_limit(self):
        """Regression test: 257 characters was rejected before TXT length followed RFC 1035."""
        record = TXTRecord(name="txt", text="a" * 257, zone=self.zone)
        record.validated_save()
        self.assertEqual(len(TXTRecord.objects.get(pk=record.pk).text), 257)

    def test_accepts_and_chunks_a_2048_bit_dkim_key(self):
        value = self._dkim_value(600)
        record = TXTRecord(name="dkim", text=value, zone=self.zone)
        record.validated_save()

        self.assertEqual([len(chunk) for chunk in record.character_strings], [255, 255, 90])
        self.assertEqual(b"".join(record.character_strings), value.encode("utf-8"))

    def test_accepts_explicit_quoted_multi_string(self):
        record = TXTRecord(name="spf", text='"v=spf1 include:_spf.example.com" "~all"', zone=self.zone)
        record.validated_save()
        self.assertEqual(record.character_strings, [b"v=spf1 include:_spf.example.com", b"~all"])

    # Escape handling (RFC 1035 §5.1) -- octets are counted on the decoded value
    def test_counts_decimal_escape_as_a_single_octet(self):
        record = TXTRecord(name="txt", text=r'"\065bc"', zone=self.zone)
        record.validated_save()
        self.assertEqual(record.character_strings, [b"Abc"])
        self.assertEqual(txt_wire_rdata_length(record.character_strings), 4)

    def test_accepts_255_octets_expressed_with_escapes(self):
        record = TXTRecord(name="txt", text='"' + r"\065" * TXT_CHARACTER_STRING_MAX_OCTETS + '"', zone=self.zone)
        record.full_clean()  # 1020 characters of presentation format, but only 255 octets on the wire

    def test_counts_decimal_escapes_above_127_as_a_single_octet(self):
        r"""Regression test: `\200` was decoded to a Unicode character and counted as two UTF-8 bytes."""
        for escape, octet in ((r"\128", 128), (r"\200", 200), (r"\255", 255)):
            with self.subTest(escape=escape):
                record = TXTRecord(name="txt", text=f'"{escape * TXT_CHARACTER_STRING_MAX_OCTETS}"', zone=self.zone)
                record.full_clean()
                self.assertEqual(record.character_strings, [bytes([octet]) * TXT_CHARACTER_STRING_MAX_OCTETS])

    def test_rejects_256_high_octet_escapes(self):
        record = TXTRecord(name="txt", text='"' + r"\200" * (TXT_CHARACTER_STRING_MAX_OCTETS + 1) + '"', zone=self.zone)
        with self.assertRaises(ValidationError) as context:
            record.full_clean()
        self.assertIn("Character-string 1 is 256 bytes (octets)", str(context.exception))

    def test_counts_typed_non_ascii_characters_as_their_utf8_bytes(self):
        record = TXTRecord(name="txt", text='"' + "é" * 128 + '"', zone=self.zone)  # 2 octets each in UTF-8
        with self.assertRaises(ValidationError) as context:
            record.full_clean()
        self.assertIn("Character-string 1 is 256 bytes (octets)", str(context.exception))

    def test_rejects_unterminated_quoted_character_string(self):
        record = TXTRecord(name="txt", text='"abc', zone=self.zone)
        with self.assertRaises(ValidationError) as context:
            record.full_clean()
        self.assertIn("Unterminated quoted character-string", str(context.exception))

    # Chunking must respect UTF-8 character boundaries
    def test_never_splits_a_multibyte_character(self):
        value = "😀" * 100  # 4 octets each
        chunk_list = split_txt_character_strings(value)
        self.assertEqual([len(chunk) for chunk in chunk_list], [252, 148])
        self.assertEqual(b"".join(chunk_list), value.encode("utf-8"))

    # Total RDATA length (16-bit RDLENGTH)
    def test_rejects_total_rdata_exceeding_65535_octets(self):
        record = TXTRecord(name="txt", text="a" * 66000, zone=self.zone)
        with self.assertRaises(ValidationError) as context:
            record.full_clean()
        self.assertIn(f"the maximum is {TXT_RDATA_MAX_OCTETS}", str(context.exception))

    # Enforcement flag
    @override_config(nautobot_dns_models__DNS_VALIDATION_LEVEL="none")
    def test_skips_length_validation_when_enforcement_disabled(self):
        record = TXTRecord(name="txt", text='"' + "a" * 300 + '"', zone=self.zone)
        record.full_clean()  # Should not raise

    @override_config(nautobot_dns_models__DNS_VALIDATION_LEVEL="none")
    def test_skips_presentation_format_parsing_when_enforcement_disabled(self):
        record = TXTRecord(name="txt", text='"abc', zone=self.zone)
        record.full_clean()  # Should not raise

    # Uniqueness digest -- asserted through a queryset filter so the stored column value is checked
    def _assert_stored_digest(self, record, text):
        self.assertTrue(TXTRecord.objects.filter(pk=record.pk, _text_hash=TXTRecord.hash_text(text)).exists())

    def test_text_hash_populated_by_validated_save(self):
        record = TXTRecord(name="txt", text="spf-record", zone=self.zone)
        record.validated_save()
        self._assert_stored_digest(record, "spf-record")

    def test_text_hash_populated_by_objects_create(self):
        """`objects.create()` calls `save()` without `clean()`, so `save()` must set the digest too."""
        record = TXTRecord.objects.create(name="txt", text="spf-record", zone=self.zone)
        self._assert_stored_digest(record, "spf-record")

    def test_text_hash_refreshed_when_text_changes(self):
        record = TXTRecord.objects.create(name="txt", text="original", zone=self.zone)
        record.text = "updated"
        record.validated_save()
        self._assert_stored_digest(record, "updated")

    def test_rejects_duplicate_name_zone_and_text(self):
        TXTRecord.objects.create(name="txt", text="spf-record", zone=self.zone)
        with self.assertRaises(ValidationError) as context:
            TXTRecord(name="txt", text="spf-record", zone=self.zone).validated_save()
        self.assertIn("TXT Record with this Name, Zone and Text already exists", str(context.exception))

    def test_allows_same_name_and_zone_with_different_text(self):
        TXTRecord(name="txt", text="spf-record", zone=self.zone).validated_save()
        TXTRecord(name="txt", text="dkim-record", zone=self.zone).validated_save()
        self.assertEqual(TXTRecord.objects.filter(name="txt", zone=self.zone).count(), 2)

    def test_long_values_differing_past_the_first_chunk_are_distinct(self):
        base = "a" * 300
        TXTRecord(name="txt", text=base + "one", zone=self.zone).validated_save()
        TXTRecord(name="txt", text=base + "two", zone=self.zone).validated_save()
        self.assertEqual(TXTRecord.objects.filter(name="txt", zone=self.zone).count(), 2)

    # Natural key must be unaffected by the digest column
    def test_natural_key_includes_text_and_not_the_digest(self):
        """Moving the unique constraint onto the digest must not change the natural key (CSV, API lookups)."""
        lookups = list(TXTRecord.natural_key_field_lookups)
        self.assertEqual(lookups[:2], ["name", "text"])
        self.assertNotIn("_text_hash", lookups)

    def test_natural_key_round_trips_a_long_value(self):
        value = self._dkim_value(600)
        record = TXTRecord.objects.create(name="dkim", text=value, zone=self.zone)
        self.assertEqual(TXTRecord.objects.get_by_natural_key(*record.natural_key()), record)


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

    def test_auto_ptr_does_not_use_catalog_reverse_zone(self):
        """A reverse-named catalog zone is not eligible to receive an automatically created PTR."""
        catalog_zone = DNSZone.objects.create(
            name="1.168.192.in-addr.arpa",
            dns_view=self.view,
            type=DNSZoneTypeChoices.TYPE_CATALOG,
        )
        with self.assertRaises(ValidationError):
            ARecord.objects.create(name="host4", ip_address=self.ipv4_unmatched, zone=self.fwd_on)
        self.assertFalse(ARecord.objects.filter(name="host4").exists())
        self.assertFalse(PTRRecord.objects.filter(zone=catalog_zone).exists())

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

    def test_does_not_use_catalog_zone(self):
        """The reverse zone lookup skips a catalog zone, falling back to a broader zone if there is one."""
        DNSZone.objects.create(
            name="0.0.10.in-addr.arpa",
            dns_view=self.view_a,
            type=DNSZoneTypeChoices.TYPE_CATALOG,
        )
        self.assertIsNone(DNSZone.find_reverse_zone_for_ptrdname("1.0.0.10.in-addr.arpa"))

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


class DNSZoneHierarchyTestCase(TestCase):
    """Test that DNSZone.parent is derived from the zone names and kept current."""

    @classmethod
    def setUpTestData(cls):
        cls.default_view = DNSView.objects.get(name="Default")
        cls.other_view = DNSView.objects.create(name="Other")

    def _create_zone(self, name, dns_view=None):
        zone = DNSZone(
            name=name,
            dns_view=dns_view or self.default_view,
            filename=f"{name}.zone",
            soa_mname="ns1.example.net",
            soa_rname="hostmaster@example.net",
        )
        zone.validated_save()
        return zone

    def _assert_parent(self, zone, expected_parent):
        zone.refresh_from_db()
        self.assertEqual(zone.parent, expected_parent)

    def test_zone_without_an_enclosing_zone_has_no_parent(self):
        zone = self._create_zone("apps.example.com")
        self.assertIsNone(zone.parent)

    def test_new_zone_takes_the_most_specific_enclosing_zone_as_parent(self):
        self._create_zone("com")
        example = self._create_zone("example.com")
        zone = self._create_zone("a.b.example.com")
        self._assert_parent(zone, example)

    def test_new_zone_adopts_existing_zones_below_it(self):
        apps = self._create_zone("apps.example.com")
        mail = self._create_zone("mail.example.com")
        example = self._create_zone("example.com")
        self._assert_parent(apps, example)
        self._assert_parent(mail, example)
        self.assertQuerySetEqual(example.children.order_by("name"), [apps, mail])

    def test_intermediate_zone_takes_over_deeper_children(self):
        example = self._create_zone("example.com")
        deep = self._create_zone("x.corp.example.com")
        sibling = self._create_zone("apps.example.com")
        corp = self._create_zone("corp.example.com")
        self._assert_parent(deep, corp)
        self._assert_parent(corp, example)
        self._assert_parent(sibling, example)

    def test_deleting_a_zone_moves_its_children_to_its_parent(self):
        example = self._create_zone("example.com")
        corp = self._create_zone("corp.example.com")
        deep = self._create_zone("x.corp.example.com")
        corp.delete()
        self._assert_parent(deep, example)

    def test_deleting_a_root_zone_leaves_its_children_without_parent(self):
        example = self._create_zone("example.com")
        apps = self._create_zone("apps.example.com")
        example.delete()
        self._assert_parent(apps, None)

    def test_queryset_delete_moves_children_to_their_new_enclosing_zone(self):
        example = self._create_zone("example.com")
        self._create_zone("corp.example.com")
        deep = self._create_zone("x.corp.example.com")
        DNSZone.objects.filter(name="corp.example.com").delete()
        self._assert_parent(deep, example)

    def test_rename_releases_former_children_and_adopts_new_ones(self):
        example = self._create_zone("example.com")
        corp = self._create_zone("corp.example.com")
        corp_host = self._create_zone("x.corp.example.com")
        lab_host = self._create_zone("x.lab.example.com")

        corp.name = "lab.example.com"
        corp.validated_save()

        self._assert_parent(corp_host, example)
        self._assert_parent(lab_host, corp)

    def test_rename_below_the_old_name_takes_the_next_enclosing_zone(self):
        com = self._create_zone("com")
        zone = self._create_zone("example.com")

        zone.name = "x.example.com"
        zone.validated_save()

        self._assert_parent(zone, com)

    def test_moving_to_another_view_updates_both_views(self):
        default_parent = self._create_zone("example.com")
        other_parent = self._create_zone("example.com", dns_view=self.other_view)
        corp = self._create_zone("corp.example.com")
        default_child = self._create_zone("x.corp.example.com")
        other_child = self._create_zone("x.corp.example.com", dns_view=self.other_view)

        corp.dns_view = self.other_view
        corp.validated_save()

        self._assert_parent(corp, other_parent)
        self._assert_parent(default_child, default_parent)
        self._assert_parent(other_child, corp)

    def test_zones_in_different_views_are_unrelated(self):
        self._create_zone("example.com", dns_view=self.other_view)
        zone = self._create_zone("apps.example.com")
        self.assertIsNone(zone.parent)

    def test_reverse_zones_form_a_hierarchy(self):
        broad = self._create_zone("168.192.in-addr.arpa")
        specific = self._create_zone("1.168.192.in-addr.arpa")
        self._assert_parent(specific, broad)

    def test_matching_ignores_case(self):
        example = self._create_zone("Example.COM")
        zone = self._create_zone("apps.example.com")
        self._assert_parent(zone, example)

    def test_wire_format_validation_rejects_a_trailing_dot(self):
        """Zone names carry no trailing root dot, so the hierarchy compares names without one."""
        with self.assertRaises(ValidationError):
            self._create_zone("example.com.")

    def test_save_repairs_parents_left_stale_in_the_same_view(self):
        """Every zone save recomputes its whole DNS View, including parents changed by writes that bypass save."""
        example = self._create_zone("example.com")
        apps = self._create_zone("apps.example.com")
        DNSZone.objects.filter(pk=apps.pk).update(parent=None)

        self._create_zone("unrelated.net")

        self._assert_parent(apps, example)

    def test_parent_is_not_writable(self):
        example = self._create_zone("example.com")
        zone = self._create_zone("other.net")
        zone.parent = example
        zone.validated_save()
        self._assert_parent(zone, None)

    def test_saving_without_renaming_or_moving_does_not_recompute_the_view(self):
        self._create_zone("example.com")
        apps = self._create_zone("apps.example.com")
        DNSZone.objects.filter(pk=apps.pk).update(parent=None)

        apps.description = "Updated"
        apps.validated_save()

        self._assert_parent(apps, None)

    def test_rebuild_zone_hierarchy_repairs_parents_set_by_bulk_writes(self):
        example = self._create_zone("example.com")
        apps = self._create_zone("apps.example.com")
        DNSZone.objects.filter(pk=apps.pk).update(parent=None)
        DNSZone.objects.filter(pk=example.pk).update(parent=apps)

        self.assertEqual(rebuild_zone_hierarchy(), 2)
        self._assert_parent(apps, example)
        self._assert_parent(example, None)
        self.assertEqual(rebuild_zone_hierarchy(), 0)

    def test_rebuild_command_reports_how_many_zones_changed(self):
        example = self._create_zone("example.com")
        apps = self._create_zone("apps.example.com")
        DNSZone.objects.filter(pk=apps.pk).update(parent=None)

        output = StringIO()
        call_command("rebuild_dns_zone_hierarchy", stdout=output)

        self.assertIn("Updated the parent of 1 DNS zone(s).", output.getvalue())
        self._assert_parent(apps, example)


class DNSDelegationTestCase(TestCase):
    """Test the DNSDelegation model and the data it derives from records."""

    @classmethod
    def setUpTestData(cls):
        cls.zone = DNSZone.objects.create(name="example.com")
        status = Status.objects.get(name="Active")
        namespace = Namespace.objects.get(name="Global")
        Prefix.objects.create(prefix="192.0.2.0/24", namespace=namespace, type="Pool", status=status)
        cls.glue_ip = IPAddress.objects.create(address="192.0.2.10/32", namespace=namespace, status=status)
        cls.sibling_ip = IPAddress.objects.create(address="192.0.2.20/32", namespace=namespace, status=status)
        cls.external_ip = IPAddress.objects.create(address="192.0.2.30/32", namespace=namespace, status=status)

    def _create_delegation(self, name="apps"):
        delegation = DNSDelegation(zone=self.zone, name=name)
        delegation.validated_save()
        return delegation

    def test_get_enclosing_zone_can_exclude_a_zone(self):
        com = DNSZone.objects.create(name="com")
        view_id = self.zone.dns_view_id

        self.assertEqual(DNSZone.get_enclosing_zone("x.example.com", view_id), self.zone)
        self.assertEqual(DNSZone.get_enclosing_zone("x.example.com", view_id, exclude_pk=self.zone.pk), com)

    def test_fqdn_and_string(self):
        delegation = self._create_delegation()
        self.assertEqual(delegation.fqdn, "apps.example.com")
        self.assertEqual(str(delegation), "apps.example.com")

    def test_rejects_a_catalog_zone(self):
        catalog_zone = create_zone("catalog.example", type=DNSZoneTypeChoices.TYPE_CATALOG)
        with self.assertRaises(ValidationError) as context:
            DNSDelegation(zone=catalog_zone, name="apps").full_clean()
        self.assertIn("zone", context.exception.message_dict)

    def test_rejects_the_zone_apex(self):
        for name in ("@", ""):
            with self.subTest(name=name), self.assertRaises(ValidationError):
                DNSDelegation(zone=self.zone, name=name).full_clean()

    def test_absolute_name_is_stored_relative_to_the_zone(self):
        delegation = self._create_delegation(name="apps.Example.com.")
        self.assertEqual(delegation.name, "apps")

    def test_absolute_name_is_normalized_by_save_without_clean(self):
        delegation = DNSDelegation.objects.create(zone=self.zone, name="apps.example.com.")
        self.assertEqual(delegation.name, "apps")

    def test_rejects_a_name_differing_only_by_case(self):
        self._create_delegation(name="apps")
        with self.assertRaises(ValidationError) as context:
            DNSDelegation(zone=self.zone, name="Apps").full_clean()
        self.assertIn("ignoring letter case", str(context.exception.message_dict["name"]))

    def test_database_rejects_a_name_differing_only_by_case(self):
        self._create_delegation(name="apps")
        with self.assertRaises(IntegrityError), transaction.atomic():
            DNSDelegation.objects.create(zone=self.zone, name="APPS")

    @override_config(nautobot_dns_models__CNAME_RESTRICTION_ENABLED=True)
    def test_cannot_share_an_owner_name_with_a_cname_ignoring_case(self):
        CNAMERecord.objects.create(name="Apps", alias="elsewhere.example.net", zone=self.zone)
        for name in ("Apps", "apps"):
            with self.subTest(name=name), self.assertRaises(ValidationError):
                DNSDelegation(zone=self.zone, name=name).full_clean()

    @override_config(nautobot_dns_models__CNAME_RESTRICTION_ENABLED=True)
    def test_cname_cannot_be_added_at_a_delegation_ignoring_case(self):
        self._create_delegation()
        for name in ("apps", "Apps"):
            with self.subTest(name=name), self.assertRaises(ValidationError):
                CNAMERecord(name=name, alias="elsewhere.example.net", zone=self.zone).full_clean()

    def test_ns_records_are_the_records_at_the_owner_name(self):
        delegation = self._create_delegation()
        at_cut = NSRecord.objects.create(name="Apps", server="ns1.apps.example.com", zone=self.zone)
        NSRecord.objects.create(name="@", server="ns1.example.net", zone=self.zone)
        NSRecord.objects.create(name="mail", server="ns1.example.net", zone=self.zone)
        self.assertQuerySetEqual(delegation.ns_records, [at_cut])

    def test_child_zone_is_the_zone_named_after_the_delegated_domain(self):
        delegation = self._create_delegation()
        self.assertIsNone(delegation.get_child_zone())
        child = DNSZone.objects.create(name="apps.example.com")
        DNSZone.objects.create(name="apps.example.com", dns_view=DNSView.objects.create(name="Other"))
        self.assertEqual(delegation.get_child_zone(), child)

    def test_classify_name_server(self):
        delegation = self._create_delegation()
        cases = (
            ("ns1.apps.example.com", NameServerRelationshipChoices.IN_DOMAIN),
            ("NS1.Apps.Example.com.", NameServerRelationshipChoices.IN_DOMAIN),
            ("apps.example.com", NameServerRelationshipChoices.IN_DOMAIN),
            ("ns.example.com", NameServerRelationshipChoices.SIBLING_DOMAIN),
            ("ns.mail.example.com", NameServerRelationshipChoices.SIBLING_DOMAIN),
            ("example.com", NameServerRelationshipChoices.SIBLING_DOMAIN),
            ("ns2.other.net", NameServerRelationshipChoices.UNRELATED),
            ("ns.notexample.com", NameServerRelationshipChoices.UNRELATED),
        )
        for server, expected in cases:
            with self.subTest(server=server):
                self.assertEqual(delegation.classify_name_server(server), expected)

    def test_glue_records_are_address_records_in_the_parent_zone(self):
        delegation = self._create_delegation()
        glue = ARecord.objects.create(name="ns1.apps", ip_address=self.glue_ip, zone=self.zone)
        self.assertEqual(get_address_records(delegation.zone, "ns1.apps.example.com."), [glue])
        self.assertEqual(get_address_records(delegation.zone, "ns2.apps.example.com"), [])
        self.assertEqual(get_address_records(delegation.zone, "ns1.other.net"), [])

    def test_glue_querysets_hold_the_address_records_of_in_zone_name_servers(self):
        delegation = self._create_delegation()
        NSRecord.objects.create(name="apps", server="ns1.apps.example.com", zone=self.zone)
        NSRecord.objects.create(name="apps", server="NS.Example.com.", zone=self.zone)
        NSRecord.objects.create(name="apps", server="ns2.other.net", zone=self.zone)
        in_domain = ARecord.objects.create(name="ns1.apps", ip_address=self.glue_ip, zone=self.zone)
        sibling = ARecord.objects.create(name="ns", ip_address=self.sibling_ip, zone=self.zone)
        ARecord.objects.create(name="www", ip_address=self.external_ip, zone=self.zone)

        self.assertQuerySetEqual(delegation.glue_a_records.order_by("name"), [sibling, in_domain])
        self.assertFalse(delegation.glue_aaaa_records.exists())

    def test_glue_querysets_are_empty_without_ns_records(self):
        delegation = self._create_delegation()
        ARecord.objects.create(name="ns1.apps", ip_address=self.glue_ip, zone=self.zone)
        self.assertFalse(delegation.glue_a_records.exists())

    def test_name_server_addresses_come_from_the_zone_that_holds_the_name(self):
        delegation = self._create_delegation()
        sibling = ARecord.objects.create(name="ns", ip_address=self.sibling_ip, zone=self.zone)
        other_zone = DNSZone.objects.create(name="other.net")
        external = ARecord.objects.create(name="ns2", ip_address=self.external_ip, zone=other_zone)

        self.assertEqual(delegation.get_name_server_addresses("ns.example.com"), [sibling])
        self.assertEqual(delegation.get_name_server_addresses("ns2.other.net"), [external])
        self.assertEqual(delegation.get_name_server_addresses("ns.unknown.org"), [])


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


class DNSZoneCatalogZoneTest(TestCase):
    """Tests for the records a catalog zone carries.

    A catalog zone holds the apex NS RRset RFC 9432 §4 requires and the version TXT record §4.2.1
    requires, both written by the app, and accepts no user-managed records.
    """

    @classmethod
    def setUpTestData(cls):
        cls.catalog_zone = create_zone("catalog.example", type=DNSZoneTypeChoices.TYPE_CATALOG)
        cls.primary_zone = create_zone("primary.example")

    def _version_record(self):
        """Return the version TXT the zone created for itself, the one record a user may not touch."""
        return TXTRecord.objects.get(name="version", zone=self.catalog_zone)

    @staticmethod
    def _unsaved_records(zone):
        """Return one unsaved instance of every record type, all owned by `zone`.

        Since the A/AAAA records do not have IPs, they are not suitable for saving.
        """
        return [
            AAAARecord(name="v6", zone=zone),
            ARecord(name="v4", zone=zone),
            CNAMERecord(name="alias", alias="target.example.", zone=zone),
            MXRecord(name="mail", mail_server="mx1.example.", zone=zone),
            NSRecord(name="sub", server="ns1.example.", zone=zone),
            PTRRecord(name="ptr", ptrdname="host.example.", zone=zone),
            SRVRecord(name="_sip._tcp", target="sip.example.", port=5060, zone=zone),
            TXTRecord(name="txt", text="value", zone=zone),
        ]

    def test_creating_catalog_zone_writes_the_apex_ns_record(self):
        """A new catalog zone gets the apex NS record `$CATZ IN NS invalid.`, whose TTL follows the zone's.

        It is the RRset that makes the catalog a valid zone (RFC 9432 §4).
        """
        record = NSRecord.objects.get(zone=self.catalog_zone)
        self.assertEqual(record.name, APEX_RECORD_NAME)
        self.assertEqual(record.server, CATALOG_APEX_NS_SERVER)
        # A TTL copied onto the record would also match the zone's at first; changing the zone's
        # TTL shows the record follows it.
        self.catalog_zone.ttl = 0
        self.catalog_zone.save()
        self.assertEqual(NSRecord.objects.get(zone=self.catalog_zone).ttl, 0)

    def test_resaving_catalog_zone_does_not_duplicate_the_apex_ns_record(self):
        """Saving a catalog zone again adds no second apex NS record.

        The RRset holds the single RR the RFC recommends.
        """
        self.catalog_zone.description = "Edited"
        self.catalog_zone.save()
        self.assertEqual(NSRecord.objects.filter(zone=self.catalog_zone).count(), 1)

    def test_saving_catalog_zone_restores_a_missing_apex_ns_record(self):
        """Saving a catalog zone restores a missing apex NS record.

        A server would refuse to load the zone without it.
        """
        with system_write():
            NSRecord.objects.filter(zone=self.catalog_zone).delete()

        self.catalog_zone.save()

        self.assertEqual(NSRecord.objects.get(zone=self.catalog_zone).server, CATALOG_APEX_NS_SERVER)

    def test_creating_catalog_zone_writes_the_version_record(self):
        """A new catalog zone gets the version record `version.$CATZ IN TXT "2"`, whose TTL follows the zone's."""
        record = TXTRecord.objects.get(zone=self.catalog_zone)
        self.assertEqual(record.name, "version")
        self.assertEqual(record.text, "2")
        # A TTL copied onto the record would also match the zone's at first; changing the zone's
        # TTL shows the record follows it.
        self.catalog_zone.ttl = 0
        self.catalog_zone.save()
        self.assertEqual(TXTRecord.objects.get(zone=self.catalog_zone).ttl, 0)

    def test_creating_primary_zone_writes_no_records(self):
        """A new primary zone gets no records."""
        for record_model in dns_record_models():
            with self.subTest(record_model=record_model.__name__):
                self.assertFalse(record_model.objects.filter(zone=self.primary_zone).exists())

    def test_resaving_catalog_zone_does_not_duplicate_the_version_record(self):
        """Saving a catalog zone again adds no second version record.

        RFC 9432 §4.2.1 allows exactly one RR in the version RRset.
        """
        self.catalog_zone.description = "Edited"
        self.catalog_zone.save()
        self.assertEqual(TXTRecord.objects.filter(name="version", zone=self.catalog_zone).count(), 1)

    def test_saving_catalog_zone_restores_a_missing_version_record(self):
        """Saving a catalog zone restores a missing version record.

        A consumer would reject the catalog without it.
        """
        with system_write():
            TXTRecord.objects.filter(zone=self.catalog_zone).delete()

        self.catalog_zone.save()

        self.assertEqual(TXTRecord.objects.get(name="version", zone=self.catalog_zone).text, "2")

    def test_rejects_user_created_record_in_catalog_zone(self):
        """Validation refuses every record type a user could try to add to a catalog zone."""
        records = self._unsaved_records(self.catalog_zone)
        # Only the records `_unsaved_records` builds are checked below, so a record model missing
        # from it would go untested.
        self.assertEqual({type(record) for record in records}, set(dns_record_models()))

        for record in records:
            with self.subTest(record_model=type(record).__name__):
                with self.assertRaises(ValidationError) as context:
                    record.full_clean()
                self.assertEqual(
                    context.exception.message_dict["zone"][0],
                    "Records in a catalog zone are system-managed and cannot be created or edited directly.",
                )

    def test_system_write_allows_record_in_catalog_zone(self):
        """The app's own sync code can write the records a user is forbidden to create."""
        with system_write():
            record = TXTRecord(name="group.nj2xg5b.zones", text="operators", zone=self.catalog_zone)
            record.validated_save()
        self.assertTrue(TXTRecord.objects.filter(pk=record.pk).exists())

    def test_rejects_edit_of_catalog_record(self):
        """An existing catalog record cannot be edited through ordinary record validation."""
        record = self._version_record()
        record.text = "1"
        with self.assertRaises(ValidationError) as context:
            record.full_clean()
        self.assertEqual(
            context.exception.message_dict["zone"][0],
            "Records in a catalog zone are system-managed and cannot be created or edited directly.",
        )

    def test_rejects_delete_of_catalog_record(self):
        """Deleting a catalog record one at a time is refused."""
        record = self._version_record()
        with self.assertRaises(ProtectedError):
            record.delete()
        self.assertTrue(TXTRecord.objects.filter(pk=record.pk).exists())

    def test_rejects_bulk_delete_of_catalog_record(self):
        """Bulk deleting a catalog record is refused.

        Bulk delete goes through `QuerySet.delete()`, which never reaches `Model.delete()`.
        """
        record = self._version_record()
        with self.assertRaises(ProtectedError):
            TXTRecord.objects.filter(pk=record.pk).delete()
        self.assertTrue(TXTRecord.objects.filter(pk=record.pk).exists())

    def test_rejects_bare_save_of_new_catalog_record(self):
        """A bare `save()`, which skips validation, refuses to create a catalog record."""
        record = TXTRecord(name="txt", text="value", zone=self.catalog_zone)

        with self.assertRaises(ValidationError) as context:
            record.save()

        self.assertEqual(
            context.exception.message_dict["zone"][0],
            "Records in a catalog zone are system-managed and cannot be created or edited directly.",
        )
        self.assertFalse(TXTRecord.objects.filter(pk=record.pk).exists())

    def test_rejects_bare_save_of_edited_catalog_record(self):
        """A bare `save()`, which skips validation, refuses to edit a catalog record."""
        record = self._version_record()
        record.text = "1"

        with self.assertRaises(ValidationError):
            record.save()

        self.assertEqual(self._version_record().text, "2")

    def test_rejects_queryset_writes_of_catalog_records(self):
        """`update()`, `bulk_update()` and `bulk_create()` refuse catalog records, and store nothing."""
        record = self._version_record()
        record.text = "1"

        test_cases = [
            ("update", lambda: TXTRecord.objects.filter(pk=record.pk).update(text="1")),
            ("bulk_update", lambda: TXTRecord.objects.bulk_update([record], ["text"])),
            (
                "bulk_create",
                lambda: TXTRecord.objects.bulk_create([TXTRecord(name="txt", text="value", zone=self.catalog_zone)]),
            ),
        ]

        for method, write_fn in test_cases:
            with self.subTest(method=method):
                with self.assertRaises(ValidationError) as context:
                    write_fn()

                self.assertEqual(
                    context.exception.message_dict["zone"][0],
                    "Records in a catalog zone are system-managed and cannot be created or edited directly.",
                )
                self.assertEqual(
                    list(TXTRecord.objects.filter(zone=self.catalog_zone).values_list("text", flat=True)), ["2"]
                )

    def test_rejects_moving_a_record_out_of_a_catalog_zone(self):
        """A catalog record cannot be moved to another zone, whichever way it is written."""
        record = self._version_record()
        record.zone = self.primary_zone

        test_cases = [
            ("full_clean", record.full_clean),
            ("save", record.save),
            ("update", lambda: TXTRecord.objects.filter(pk=record.pk).update(zone=self.primary_zone)),
            ("bulk_update", lambda: TXTRecord.objects.bulk_update([record], ["zone"])),
        ]

        for method, move_fn in test_cases:
            with self.subTest(method=method):
                with self.assertRaises(ValidationError):
                    move_fn()

                self.assertEqual(TXTRecord.objects.get(pk=record.pk).zone_id, self.catalog_zone.pk)

    def test_rejects_moving_a_record_into_a_catalog_zone(self):
        """A record cannot be moved into a catalog zone, whichever way it is written."""
        record = NSRecord(name="sub", server="ns1.example.", zone=self.primary_zone)
        record.validated_save()
        record.zone = self.catalog_zone

        test_cases = [
            ("full_clean", record.full_clean),
            ("save", record.save),
            ("update", lambda: NSRecord.objects.filter(pk=record.pk).update(zone=self.catalog_zone)),
            ("update by id", lambda: NSRecord.objects.filter(pk=record.pk).update(zone_id=self.catalog_zone.pk)),
            ("bulk_update", lambda: NSRecord.objects.bulk_update([record], ["zone"])),
        ]

        for method, move_fn in test_cases:
            with self.subTest(method=method):
                with self.assertRaises(ValidationError):
                    move_fn()

                self.assertEqual(NSRecord.objects.get(pk=record.pk).zone_id, self.primary_zone.pk)

    def test_system_write_allows_queryset_writes_of_catalog_records(self):
        """The app's own sync code can write catalog records through a queryset."""
        record = self._version_record()

        with system_write():
            TXTRecord.objects.filter(pk=record.pk).update(description="Edited")

        self.assertEqual(self._version_record().description, "Edited")

    def test_system_write_allows_delete_of_catalog_record(self):
        """The app's own sync code can remove the records a user is forbidden to delete."""
        record = self._version_record()
        with system_write():
            record.delete()
        self.assertFalse(TXTRecord.objects.filter(pk=record.pk).exists())

    def test_deleting_catalog_zone_removes_its_records(self):
        """Deleting a catalog zone removes its records.

        The records refuse user deletes, but the zone stays deletable.
        """
        record = self._version_record()
        self.catalog_zone.delete()
        self.assertFalse(DNSZone.objects.filter(pk=self.catalog_zone.pk).exists())
        self.assertFalse(TXTRecord.objects.filter(pk=record.pk).exists())

    def test_bulk_deleting_catalog_zone_removes_its_records(self):
        """Bulk deleting a catalog zone removes its records.

        This is the `QuerySet.delete()` path Nautobot's bulk delete job uses.
        """
        record = self._version_record()
        DNSZone.objects.filter(pk=self.catalog_zone.pk).delete()
        self.assertFalse(DNSZone.objects.filter(pk=self.catalog_zone.pk).exists())
        self.assertFalse(TXTRecord.objects.filter(pk=record.pk).exists())


class CatalogZoneWriteGuardQueryTest(TestCase):
    """Tests for the queries the catalog zone write guard adds to record writes outside a catalog zone."""

    @classmethod
    def setUpTestData(cls):
        cls.primary_zone = create_zone("primary.example")
        cls.other_primary_zone = create_zone("other.example")
        status = Status.objects.get(name="Active")
        namespace = Namespace.objects.get(name="Global")
        Prefix.objects.create(prefix="10.0.0.0/24", namespace=namespace, type="Pool", status=status)
        cls.ip_address = IPAddress.objects.create(address="10.0.0.1/32", namespace=namespace, status=status)

    def setUp(self):
        # A generator which yields unique record names for each test
        self.unused_record_names = (f"host{index}" for index in itertools.count())

    def _num_queries_added_by_guard(self, write_fn):
        """Return how many more queries `write_fn` issues than under `system_write()`, which skips the guard."""
        with system_write():
            write_fn()
        with CaptureQueriesContext(connection) as guarded:
            write_fn()
        with system_write(), CaptureQueriesContext(connection) as unguarded:
            write_fn()

        return len(guarded) - len(unguarded)

    def test_creating_a_record_adds_no_query(self):
        """Creating a record checks its zone in memory, and has no stored row to check."""
        test_cases = [
            (
                "TXTRecord",
                lambda: TXTRecord(
                    name=next(self.unused_record_names), text="value", zone=self.primary_zone
                ).validated_save(),
            ),
            (
                "ARecord",
                lambda: ARecord(
                    name=next(self.unused_record_names), ip_address=self.ip_address, zone=self.primary_zone
                ).validated_save(),
            ),
        ]

        for model, write_fn in test_cases:
            with self.subTest(model=model):
                self.assertEqual(self._num_queries_added_by_guard(write_fn), 0)

    def test_editing_a_record_adds_one_query_per_check(self):
        """Each check of an edit reads the stored row: `clean()` and `save()`, and `clean()` again in `ARecord.save()`."""
        txt_record = TXTRecord(name="txt", text="value", zone=self.primary_zone)
        txt_record.validated_save()
        a_record = ARecord(name="a", ip_address=self.ip_address, zone=self.primary_zone)
        a_record.validated_save()

        test_cases = [
            ("TXTRecord", txt_record.validated_save, 2),
            ("ARecord", a_record.validated_save, 3),
        ]

        for model, write_fn, num_expected_queries in test_cases:
            with self.subTest(model=model):
                self.assertEqual(self._num_queries_added_by_guard(write_fn), num_expected_queries)

    def test_queryset_write_checks_do_not_grow_with_the_record_count(self):
        """`bulk_create()` and `update()` check once; `bulk_update()` checks up front and again in its `update()`.

        The records span two zones, so a check per record or per zone would show. Each write succeeds,
        since the records are outside a catalog.
        """
        zones = [self.primary_zone, self.other_primary_zone, self.primary_zone]
        records = NSRecord.objects.bulk_create(
            [NSRecord(name=next(self.unused_record_names), server="ns1.example.", zone=zone) for zone in zones]
        )
        pks = [record.pk for record in records]

        test_cases = [
            (
                "bulk_create",
                lambda: NSRecord.objects.bulk_create(
                    [NSRecord(name=next(self.unused_record_names), server="ns1.example.", zone=zone) for zone in zones]
                ),
                1,
            ),
            ("update", lambda: NSRecord.objects.filter(pk__in=pks).update(zone=self.primary_zone), 1),
            ("bulk_update", lambda: NSRecord.objects.bulk_update(records, ["zone"]), 2),
        ]

        for method, write_fn, num_expected_queries in test_cases:
            with self.subTest(method=method):
                self.assertEqual(self._num_queries_added_by_guard(write_fn), num_expected_queries)


def member_ptr_records(catalog_zone):
    """Return the `(owner name, PTRDNAME)` pairs of the member PTR records published in `catalog_zone`."""
    return set(PTRRecord.objects.filter(zone=catalog_zone).values_list("name", "ptrdname"))


def write_bypassing_guards(zone_pk, **fields):
    """Write `fields` to a zone row with nothing but the database to refuse them."""
    QuerySet.update(DNSZone.objects.filter(pk=zone_pk), **fields)


class CatalogMembershipTest(TestCase):
    """Tests for membership of a catalog zone through `DNSZone.catalog_zone`.

    Covers adding, removing, moving and renaming a member, the view a catalog shares with its members,
    deletion, the queryset paths that write zones without saving each one, and where a membership
    change is recorded.
    """

    @classmethod
    def setUpTestData(cls):
        cls.catalog_zone = create_zone("catalog.example", type=DNSZoneTypeChoices.TYPE_CATALOG)
        cls.other_catalog = create_zone("other-catalog.example", type=DNSZoneTypeChoices.TYPE_CATALOG)
        cls.other_view = DNSView.objects.create(name="Other")

    def test_a_zone_outside_a_catalog_has_no_label(self):
        """A zone outside a catalog has no member label."""
        zone = create_zone("member.example")

        self.assertEqual(zone.member_label, "")
        self.assertIsNone(zone.ptr_record_name)

    def test_adding_a_zone_generates_a_label_and_publishes_the_member(self):
        """Adding a zone to a catalog gives it a label and publishes its PTR record.

        RFC 9432 §4.1 publishes each member as a PTR at `<label>.zones`. Its TTL follows the
        catalog zone's.
        """
        zone = create_zone("member.example", catalog_zone=self.catalog_zone)

        self.assertEqual(len(zone.member_label), 26)
        self.assertEqual(zone.ptr_record_name, f"{zone.member_label}.zones")
        record = PTRRecord.objects.get(zone=self.catalog_zone)
        self.assertEqual((record.name, record.ptrdname), (zone.ptr_record_name, "member.example"))
        # A TTL copied onto the record would also match the zone's at first; changing the zone's
        # TTL shows the record follows it.
        self.catalog_zone.ttl = 0
        self.catalog_zone.save()
        self.assertEqual(PTRRecord.objects.get(zone=self.catalog_zone).ttl, 0)

    def test_adding_through_validation_keeps_the_label_clean_assigned(self):
        """`save()` stores the label that `clean()` assigned and validated."""
        zone = DNSZone(
            name="member.example",
            filename="member.zone",
            soa_mname="ns1.member.example.",
            soa_rname="admin@member.example",
            catalog_zone=self.catalog_zone,
        )
        zone.full_clean()
        original_label = zone.member_label

        zone.save()

        zone.refresh_from_db()
        self.assertEqual(zone.member_label, original_label)

    def test_the_member_ptr_is_system_managed(self):
        """A user cannot delete a member's PTR record on its own."""
        create_zone("member.example", catalog_zone=self.catalog_zone)

        with self.assertRaises(ProtectedError):
            PTRRecord.objects.get(zone=self.catalog_zone).delete()

    def test_a_supplied_label_is_kept_when_the_zone_is_added(self):
        """A label supplied by code is kept when the zone is added to a catalog.

        RFC 9432 lets the producer choose labels.
        """
        zone = create_zone("member.example", catalog_zone=self.catalog_zone, member_label="chosen")

        self.assertEqual(zone.member_label, "chosen")
        self.assertEqual(member_ptr_records(self.catalog_zone), {("chosen.zones", "member.example")})

    def test_an_edited_label_republishes_the_member(self):
        """An edited label on a member that stays in its catalog moves its PTR record to the new label.

        RFC 9432 §5.6 resets a member by giving it a new label.
        """
        zone = create_zone("member.example", catalog_zone=self.catalog_zone)

        for method, label in (("validated_save", "edited"), ("save", "edited-again")):
            with self.subTest(method=method):
                zone.member_label = label
                getattr(zone, method)()

                zone.refresh_from_db()
                self.assertEqual(zone.member_label, label)
                self.assertEqual(member_ptr_records(self.catalog_zone), {(f"{label}.zones", "member.example")})

    def test_a_cleared_label_is_replaced_by_a_generated_one(self):
        """Clearing a member's label gives it a new generated label rather than none."""
        zone = create_zone("member.example", catalog_zone=self.catalog_zone, member_label="chosen")

        zone.member_label = ""
        zone.validated_save()

        zone.refresh_from_db()
        self.assertNotIn(zone.member_label, ("", "chosen"))
        self.assertEqual(member_ptr_records(self.catalog_zone), {(f"{zone.member_label}.zones", "member.example")})

    def test_a_label_is_refused_outside_a_catalog(self):
        """A label supplied on a zone outside any catalog is refused."""
        outsider = create_zone("outsider.example")
        new_zone = DNSZone(
            name="new.example",
            filename="new.example.zone",
            soa_mname="ns1.new.example.",
            soa_rname="admin@new.example",
            member_label="chosen",
        )
        outsider.member_label = "chosen"

        for zone in (new_zone, outsider):
            for method in ("validated_save", "save"):
                with self.subTest(zone=zone.name, method=method):
                    with self.assertRaises(ValidationError):
                        getattr(zone, method)()

        self.assertFalse(DNSZone.objects.filter(name="new.example").exists())
        self.assertEqual(DNSZone.objects.get(pk=outsider.pk).member_label, "")

    def test_resaving_a_member_publishes_no_duplicate(self):
        """Saving a member again publishes no second PTR record."""
        zone = create_zone("member.example", catalog_zone=self.catalog_zone)

        zone.validated_save()

        self.assertEqual(PTRRecord.objects.filter(zone=self.catalog_zone).count(), 1)

    def test_resaving_a_member_restores_a_lost_ptr(self):
        """Saving a member restores a lost PTR record."""
        zone = create_zone("member.example", catalog_zone=self.catalog_zone)
        with system_write():
            PTRRecord.objects.filter(zone=self.catalog_zone).delete()

        zone.validated_save()

        self.assertEqual(member_ptr_records(self.catalog_zone), {(zone.ptr_record_name, "member.example")})

    def test_rejects_a_member_label_with_a_dot(self):
        """A member label containing a dot is refused."""
        zone = DNSZone(name="member.example", catalog_zone=self.catalog_zone, member_label="two.labels")

        with self.assertRaises(ValidationError) as context:
            zone.save()

        self.assertEqual(
            context.exception.message_dict["member_label"][0],
            "The member label must be a single DNS label, without dots.",
        )

    def test_a_zone_cannot_be_added_to_a_non_catalog_zone(self):
        """A zone cannot be added to a zone that is not a catalog zone."""
        primary_zone = create_zone("primary.example")
        zone = DNSZone(name="member.example", catalog_zone=primary_zone)

        with self.assertRaises(ValidationError) as context:
            zone.full_clean()
        self.assertIn("catalog_zone", context.exception.message_dict)

        with self.assertRaises(ValidationError) as context:
            zone.save()
        self.assertEqual(
            context.exception.message_dict["catalog_zone"][0],
            "Zones can only be members of a catalog zone.",
        )

    def test_a_catalog_zone_cannot_be_added_to_a_catalog_zone(self):
        """A catalog zone cannot be added to another catalog zone.

        RFC 9432 says nothing about nesting, but few consumers support it and we forbid it.
        """
        zone = DNSZone(name="nested.example", type=DNSZoneTypeChoices.TYPE_CATALOG, catalog_zone=self.catalog_zone)

        with self.assertRaises(ValidationError) as context:
            zone.save()

        self.assertEqual(
            context.exception.message_dict["catalog_zone"][0],
            "A catalog zone cannot be a member of another catalog zone.",
        )

    def test_a_zone_cannot_be_added_to_a_catalog_zone_in_a_different_view(self):
        """A zone cannot be added to a catalog zone in a different view.

        A catalog and its members share a view, which is what a consumer of the catalog serves.
        """
        zone = DNSZone(
            name="member.example",
            dns_view=self.other_view,
            catalog_zone=self.catalog_zone,
        )

        with self.assertRaises(ValidationError) as context:
            zone.save()

        self.assertEqual(
            context.exception.message_dict["catalog_zone"][0],
            "The catalog zone must be in the same view as this zone.",
        )

    def test_a_catalog_moved_after_validation_is_refused_on_save(self):
        """A catalog moved to another view after validation is refused on save.

        `save()` reads the catalog's view again under a lock.
        """
        zone = create_zone("member.example")
        zone.catalog_zone = self.catalog_zone
        zone.full_clean()
        DNSZone.objects.filter(pk=self.catalog_zone.pk).update(dns_view=self.other_view)

        with self.assertRaises(ValidationError) as context:
            zone.save()

        self.assertEqual(
            context.exception.message_dict["catalog_zone"][0],
            "The catalog zone must be in the same view as this zone.",
        )
        self.assertFalse(PTRRecord.objects.filter(zone=self.catalog_zone).exists())

    def test_a_catalog_deleted_after_validation_is_refused_on_save(self):
        """A catalog deleted after validation is refused on save as a validation error.

        Without the check, the write would fail with an `IntegrityError` at commit.
        """
        empty_catalog = create_zone("empty.example", type=DNSZoneTypeChoices.TYPE_CATALOG)
        zone = create_zone("member.example")
        zone.catalog_zone = empty_catalog
        zone.full_clean()
        DNSZone.objects.filter(pk=empty_catalog.pk).delete()

        with self.assertRaises(ValidationError) as context:
            zone.save()

        self.assertEqual(context.exception.message_dict["catalog_zone"][0], "The catalog zone no longer exists.")

    def test_rejects_a_label_reused_in_another_case_within_one_catalog(self):
        """A label reused in another case within one catalog is refused.

        RFC 4343 §3 compares labels without regard to case, so both name one node.
        """
        create_zone("first.example", catalog_zone=self.catalog_zone, member_label="shared")
        zone = DNSZone(
            name="second.example",
            filename="second.zone",
            soa_mname="ns1.second.example.",
            soa_rname="admin@second.example",
            catalog_zone=self.catalog_zone,
            member_label="Shared",
        )

        with self.assertRaises(ValidationError) as context:
            zone.full_clean()

        self.assertEqual(
            context.exception.message_dict,
            {"member_label": ["This label is already used by another member of the catalog zone."]},
        )

    def test_the_database_refuses_a_label_reused_in_another_case(self):
        """The database refuses a label reused in another case on a bare save."""
        create_zone("first.example", catalog_zone=self.catalog_zone, member_label="shared")

        with self.assertRaises(IntegrityError), transaction.atomic():
            create_zone("second.example", catalog_zone=self.catalog_zone, member_label="Shared")

        self.assertEqual(PTRRecord.objects.filter(zone=self.catalog_zone).count(), 1)

    def test_allows_the_same_label_in_a_different_catalog(self):
        """The same label is allowed in a different catalog."""
        create_zone("first.example", catalog_zone=self.catalog_zone, member_label="shared")

        create_zone("second.example", catalog_zone=self.other_catalog, member_label="shared")

        self.assertEqual(DNSZone.objects.filter(member_label="shared").count(), 2)

    def test_the_database_refuses_adding_a_catalog_zone_to_a_catalog_zone(self):
        """The database refuses adding a catalog zone to a catalog zone when validation is skipped."""
        nested_catalog = create_zone("nested.example", type=DNSZoneTypeChoices.TYPE_CATALOG)

        with self.assertRaises(IntegrityError), transaction.atomic():
            write_bypassing_guards(nested_catalog.pk, catalog_zone=self.catalog_zone, member_label="nested")

    def test_the_database_refuses_a_member_without_a_label(self):
        """The database refuses a member with a blank label."""
        zone = create_zone("member.example")

        with self.assertRaises(IntegrityError), transaction.atomic():
            write_bypassing_guards(zone.pk, catalog_zone=self.catalog_zone)

    def test_the_natural_key_is_the_name_and_view(self):
        """A zone's natural key stays its name and view despite the membership constraints."""
        self.assertEqual(DNSZone.natural_key_field_lookups, ["name", "dns_view__name"])

    def test_removing_withdraws_the_member_and_clears_the_label(self):
        """Removing a zone from a catalog withdraws its PTR record and clears its label.

        RFC 9432 §5.2 removes a member by withdrawing its PTR.
        """
        zone = create_zone("member.example", catalog_zone=self.catalog_zone)

        zone.catalog_zone = None
        zone.validated_save()

        zone.refresh_from_db()
        self.assertEqual(zone.member_label, "")
        self.assertEqual(member_ptr_records(self.catalog_zone), set())

    def test_moving_between_catalogs_publishes_under_a_new_label(self):
        """Moving to another catalog publishes the zone under a new label."""
        zone = create_zone("member.example", catalog_zone=self.catalog_zone)
        original_label = zone.member_label

        zone.catalog_zone = self.other_catalog
        zone.validated_save()

        self.assertNotEqual(zone.member_label, original_label)
        self.assertEqual(member_ptr_records(self.catalog_zone), set())
        self.assertEqual(member_ptr_records(self.other_catalog), {(zone.ptr_record_name, "member.example")})

    def test_removing_zone_and_adding_it_back_gives_it_a_new_label(self):
        """A zone removed from a catalog and added again gets a new label.

        It does not resume the consumer state it had.
        """
        zone = create_zone("member.example", catalog_zone=self.catalog_zone)
        original_label = zone.member_label

        zone.catalog_zone = None
        zone.validated_save()
        zone.catalog_zone = self.catalog_zone
        zone.validated_save()

        self.assertNotEqual(zone.member_label, original_label)

    def test_renaming_a_member_republishes_it_under_a_new_label(self):
        """Renaming a member republishes it under a new label."""
        zone = create_zone("member.example", catalog_zone=self.catalog_zone)
        original_label = zone.member_label

        zone.name = "renamed.example"
        zone.validated_save()

        self.assertNotEqual(zone.member_label, original_label)
        self.assertEqual(member_ptr_records(self.catalog_zone), {(zone.ptr_record_name, "renamed.example")})

    def test_renaming_one_member_leaves_the_other_members_alone(self):
        """Renaming one member leaves the other members' PTR records alone."""
        zone = create_zone("member.example", catalog_zone=self.catalog_zone)

        other_zone = create_zone("other.example", catalog_zone=self.catalog_zone)

        zone.name = "renamed.example"
        zone.validated_save()

        self.assertIn((other_zone.ptr_record_name, "other.example"), member_ptr_records(self.catalog_zone))

    def test_renaming_through_update_fields_republishes_it(self):
        """Renaming with `update_fields=["name"]` also stores the new label."""
        zone = create_zone("member.example", catalog_zone=self.catalog_zone)
        original_label = zone.member_label

        zone.name = "renamed.example"
        zone.save(update_fields=["name"])

        zone.refresh_from_db()
        self.assertNotEqual(zone.member_label, original_label)
        self.assertEqual(member_ptr_records(self.catalog_zone), {(zone.ptr_record_name, "renamed.example")})

    def test_saving_without_the_name_keeps_the_membership(self):
        """A name left out of `update_fields` is not stored, so the member is not republished."""
        zone = create_zone("member.example", catalog_zone=self.catalog_zone)
        original_label = zone.member_label

        zone.name = "renamed.example"
        zone.description = "changed"
        zone.save(update_fields=["description"])

        zone.refresh_from_db()
        self.assertEqual((zone.name, zone.member_label), ("member.example", original_label))
        self.assertEqual(member_ptr_records(self.catalog_zone), {(f"{original_label}.zones", "member.example")})

    def test_saving_without_the_catalog_keeps_the_stored_catalog(self):
        """A catalog left out of `update_fields` is not stored, so the zone stays where it was."""
        zone = create_zone("member.example", catalog_zone=self.catalog_zone)
        original_label = zone.member_label

        zone.catalog_zone = self.other_catalog
        zone.save(update_fields=["description"])

        zone.refresh_from_db()
        self.assertEqual((zone.catalog_zone, zone.member_label), (self.catalog_zone, original_label))
        self.assertEqual(member_ptr_records(self.other_catalog), set())

    def test_saving_without_the_view_keeps_the_stored_view(self):
        """A view left out of `update_fields` is not stored or checked against the catalog's."""
        zone = create_zone("member.example", catalog_zone=self.catalog_zone)

        zone.dns_view = self.other_view
        zone.description = "changed"
        zone.save(update_fields=["description"])

        zone.refresh_from_db()
        self.assertEqual((zone.dns_view, zone.description), (self.catalog_zone.dns_view, "changed"))

    def test_saving_the_catalog_zone_leaves_its_members_alone(self):
        """Saving a catalog zone maintains its apex records and leaves its members alone."""
        zone = create_zone("member.example", catalog_zone=self.catalog_zone)
        original_label = zone.member_label

        self.catalog_zone.description = "changed"
        self.catalog_zone.validated_save()

        self.assertEqual(member_ptr_records(self.catalog_zone), {(f"{original_label}.zones", "member.example")})

    def test_a_member_cannot_move_to_another_view(self):
        """A member cannot move to another view.

        Its catalog stays behind, so the pair would span views.
        """
        zone = create_zone("member.example", catalog_zone=self.catalog_zone)
        zone.dns_view = self.other_view

        with self.assertRaises(ValidationError) as context:
            zone.validated_save()

        self.assertEqual(
            context.exception.message_dict["catalog_zone"][0],
            "The catalog zone must be in the same view as this zone.",
        )

    def test_a_member_cannot_move_to_another_view_on_a_bare_save(self):
        """A member cannot move to another view on a bare save either."""
        zone = create_zone("member.example", catalog_zone=self.catalog_zone)
        zone.dns_view = self.other_view

        with self.assertRaises(ValidationError):
            zone.save()

        zone.refresh_from_db()
        self.assertNotEqual(zone.dns_view, self.other_view)

    def test_a_member_can_move_while_being_removed_from_its_catalog(self):
        """A member can move to another view in the save that clears its catalog."""
        zone = create_zone("member.example", catalog_zone=self.catalog_zone)
        zone.catalog_zone = None
        zone.dns_view = self.other_view

        zone.validated_save()

        self.assertEqual(member_ptr_records(self.catalog_zone), set())

    def test_a_catalog_with_members_cannot_move_to_another_view(self):
        """A catalog with members cannot move to another view."""
        create_zone("member.example", catalog_zone=self.catalog_zone)
        self.catalog_zone.dns_view = self.other_view

        with self.assertRaises(ValidationError) as context:
            self.catalog_zone.validated_save()

        self.assertEqual(
            context.exception.message_dict["dns_view"][0],
            "A catalog zone with members cannot be moved to another view.",
        )

    def test_a_catalog_zone_without_members_can_move_to_another_view(self):
        """A catalog zone without members can move to another view."""
        self.catalog_zone.dns_view = self.other_view

        self.catalog_zone.validated_save()

    def test_deleting_a_member_withdraws_it(self):
        """Deleting a member withdraws its PTR record."""
        zone = create_zone("member.example", catalog_zone=self.catalog_zone)

        zone.delete()

        self.assertEqual(member_ptr_records(self.catalog_zone), set())

    def test_bulk_deleting_members_withdraws_them(self):
        """Bulk deleting members withdraws their PTR records.

        This is the `QuerySet.delete()` path Nautobot's bulk delete job uses.
        """
        create_zone("first.example", catalog_zone=self.catalog_zone)
        create_zone("second.example", catalog_zone=self.catalog_zone)

        DNSZone.objects.filter(catalog_zone=self.catalog_zone).delete()

        self.assertEqual(member_ptr_records(self.catalog_zone), set())

    def test_a_catalog_with_members_cannot_be_deleted(self):
        """A catalog with members cannot be deleted, and its records survive.

        `PROTECT` on `catalog_zone` refuses the delete.
        """
        create_zone("member.example", catalog_zone=self.catalog_zone)

        with self.assertRaises(ProtectedError):
            self.catalog_zone.delete()

        self.assertTrue(DNSZone.objects.filter(pk=self.catalog_zone.pk).exists())
        self.assertEqual(PTRRecord.objects.filter(zone=self.catalog_zone).count(), 1)
        self.assertTrue(TXTRecord.objects.filter(zone=self.catalog_zone, name="version").exists())

    def test_a_refused_bulk_delete_keeps_the_catalog_records(self):
        """A refused bulk delete keeps the catalog's records.

        The record purge is rolled back with the refused delete.
        """
        create_zone("member.example", catalog_zone=self.catalog_zone)

        with self.assertRaises(ProtectedError):
            DNSZone.objects.filter(pk=self.catalog_zone.pk).delete()

        self.assertEqual(PTRRecord.objects.filter(zone=self.catalog_zone).count(), 1)
        self.assertTrue(NSRecord.objects.filter(zone=self.catalog_zone).exists())

    def test_update_refuses_the_membership_fields(self):
        """`update()` refuses the membership fields.

        An update would store a membership the catalog never publishes.
        """
        zone = create_zone("member.example")

        with self.assertRaises(ValidationError) as context:
            DNSZone.objects.filter(pk=zone.pk).update(catalog_zone=self.catalog_zone)

        self.assertEqual(
            context.exception.messages[0],
            "These fields cannot be written through update() or bulk_update(); save each zone instead: catalog_zone.",
        )

    def test_bulk_update_refuses_the_membership_fields(self):
        """`bulk_update()` refuses the membership fields, and stores nothing.

        A relabel would leave the PTR record published where nothing can find it to withdraw, and
        adding a zone would store a membership the catalog never publishes.
        """
        member = create_zone("member.example", catalog_zone=self.catalog_zone)
        outsider = create_zone("outsider.example")
        member.member_label = "relabelled"
        outsider.catalog_zone = self.catalog_zone

        test_cases = [
            (member, "member_label"),
            (outsider, "catalog_zone"),
            (outsider, "catalog_zone_id"),
        ]

        for zone, field in test_cases:
            with self.subTest(field=field):
                stored = DNSZone.objects.values("catalog_zone_id", "member_label").get(pk=zone.pk)

                with self.assertRaises(ValidationError):
                    DNSZone.objects.bulk_update([zone], [field])

                self.assertEqual(DNSZone.objects.values("catalog_zone_id", "member_label").get(pk=zone.pk), stored)

    def test_queryset_renames_refuse_a_member(self):
        """`update()` and `bulk_update()` refuse to rename a member, and store nothing.

        The member's PTR record names it, and a rename gives it a new label.
        """
        member = create_zone("member.example", catalog_zone=self.catalog_zone)
        member.name = "renamed.example"
        published = member_ptr_records(self.catalog_zone)

        test_cases = [
            ("update", lambda: DNSZone.objects.filter(pk=member.pk).update(name="renamed.example")),
            ("bulk_update", lambda: DNSZone.objects.bulk_update([member], ["name"])),
        ]

        for method, rename_fn in test_cases:
            with self.subTest(method=method):
                with self.assertRaises(ValidationError):
                    rename_fn()

                self.assertEqual(DNSZone.objects.get(pk=member.pk).name, "member.example")
                self.assertEqual(member_ptr_records(self.catalog_zone), published)

    def test_queryset_renames_allow_a_zone_outside_a_catalog(self):
        """`update()` and `bulk_update()` rename a zone in no catalog."""
        outsider = create_zone("outsider.example")

        DNSZone.objects.filter(pk=outsider.pk).update(name="renamed.example")
        outsider.name = "renamed-again.example"
        DNSZone.objects.bulk_update([outsider], ["name"])

        self.assertEqual(DNSZone.objects.get(pk=outsider.pk).name, "renamed-again.example")

    def test_queryset_view_moves_refuse_members_and_catalogs_with_members(self):
        """`update()` and `bulk_update()` refuse to move a member, or a catalog with members, to another view.

        A catalog and its members must share a view, which only `save()` checks.
        """
        member = create_zone("member.example", catalog_zone=self.catalog_zone)
        member.dns_view = self.other_view
        catalog = DNSZone.objects.get(pk=self.catalog_zone.pk)
        catalog.dns_view = self.other_view

        test_cases = [
            ("member", "update", lambda: DNSZone.objects.filter(pk=member.pk).update(dns_view=self.other_view)),
            ("member", "bulk_update", lambda: DNSZone.objects.bulk_update([member], ["dns_view"])),
            ("catalog", "update", lambda: DNSZone.objects.filter(pk=catalog.pk).update(dns_view=self.other_view)),
            ("catalog", "bulk_update", lambda: DNSZone.objects.bulk_update([catalog], ["dns_view"])),
        ]

        for zone, method, move_fn in test_cases:
            with self.subTest(zone=zone, method=method):
                with self.assertRaises(ValidationError):
                    move_fn()

                self.assertFalse(DNSZone.objects.filter(dns_view=self.other_view).exists())

    def test_queryset_view_moves_allow_zones_outside_a_catalog_and_empty_catalogs(self):
        """`update()` and `bulk_update()` move a zone in no catalog, and a catalog without members, to another view."""
        outsider = create_zone("outsider.example")

        DNSZone.objects.filter(pk=outsider.pk).update(dns_view=self.other_view)
        self.other_catalog.dns_view = self.other_view
        DNSZone.objects.bulk_update([self.other_catalog], ["dns_view"])

        self.assertEqual(
            set(DNSZone.objects.filter(dns_view=self.other_view).values_list("pk", flat=True)),
            {outsider.pk, self.other_catalog.pk},
        )

    def test_bulk_create_refuses_a_member(self):
        """`bulk_create()` refuses a member.

        It reaches no `save()`, so the member would get neither a label nor a PTR record.
        """
        zone = DNSZone(name="member.example", catalog_zone=self.catalog_zone)

        with self.assertRaises(ValidationError):
            DNSZone.objects.bulk_create([zone])

    def test_bulk_create_accepts_zones_outside_a_catalog(self):
        """`bulk_create()` accepts zones outside a catalog."""
        DNSZone.objects.bulk_create([DNSZone(name="member.example")])

        self.assertTrue(DNSZone.objects.filter(name="member.example").exists())

    def test_the_database_refuses_a_bulk_add_through_the_related_manager(self):
        """The database refuses `members.add()` without `bulk=False`.

        It updates through the base manager, past the queryset guard, and stores no label.
        """
        zone = create_zone("member.example")

        with self.assertRaises(IntegrityError), transaction.atomic():
            self.catalog_zone.members.add(zone)

    def test_the_related_manager_saves_each_zone_without_bulk(self):
        """`members.add()` and `members.remove()` with `bulk=False` publish and withdraw the member."""
        zone = create_zone("member.example")

        self.catalog_zone.members.add(zone, bulk=False)
        zone.refresh_from_db()
        self.assertEqual(member_ptr_records(self.catalog_zone), {(zone.ptr_record_name, "member.example")})

        self.catalog_zone.members.remove(zone, bulk=False)
        self.assertEqual(member_ptr_records(self.catalog_zone), set())

    def test_adding_is_recorded_against_the_member_zone(self):
        """Adding a zone to a catalog is recorded as a change of the zone."""
        zone = create_zone("member.example")

        with web_request_context(self.user):
            zone.catalog_zone = self.catalog_zone
            zone.validated_save()

        change = ObjectChange.objects.get(changed_object_id=zone.pk)
        self.assertEqual(change.object_data_v2["catalog_zone"]["id"], str(self.catalog_zone.pk))
        self.assertEqual(change.object_data_v2["member_label"], zone.member_label)

    def test_adding_records_no_change_against_the_catalog_zone(self):
        """Adding a zone records no change against the catalog zone, only against its PTR record."""
        zone = create_zone("member.example")

        with web_request_context(self.user):
            zone.catalog_zone = self.catalog_zone
            zone.validated_save()

        self.assertFalse(ObjectChange.objects.filter(changed_object_id=self.catalog_zone.pk).exists())
        ptr_type = ContentType.objects.get_for_model(PTRRecord)
        self.assertEqual(
            list(ObjectChange.objects.filter(changed_object_type=ptr_type).values_list("action", "object_repr")),
            [("create", "member.example")],
        )

    def test_renaming_a_member_records_a_withdrawal_and_an_addition(self):
        """Renaming a member records its old PTR record deleted and a new one created."""
        zone = create_zone("member.example", catalog_zone=self.catalog_zone)

        with web_request_context(self.user):
            zone.name = "renamed.example"
            zone.validated_save()

        ptr_type = ContentType.objects.get_for_model(PTRRecord)
        self.assertEqual(
            set(ObjectChange.objects.filter(changed_object_type=ptr_type).values_list("action", "object_repr")),
            {("delete", "member.example"), ("create", "renamed.example")},
        )


class DNSForwarderTestCase(TestCase):
    """Test the DNSForwarder model."""

    @classmethod
    def setUpTestData(cls):
        status = Status.objects.get(name="Active")
        namespace = Namespace.objects.get(name="Global")
        Prefix.objects.create(prefix="192.0.2.0/24", namespace=namespace, type="Pool", status=status)
        cls.ip_address = IPAddress.objects.create(address="192.0.2.53/32", namespace=namespace, status=status)

    def test_address_from_ipam(self):
        forwarder = DNSForwarder(name="Corp resolver", ip_address=self.ip_address)
        forwarder.validated_save()
        self.assertEqual(forwarder.get_address(), "192.0.2.53")
        self.assertEqual(forwarder.port, 53)
        self.assertEqual(str(forwarder), "Corp resolver")

    def test_literal_address(self):
        forwarder = DNSForwarder(name="Quad9", address="2620:fe::fe", port=853)
        forwarder.validated_save()
        self.assertEqual(forwarder.get_address(), "2620:fe::fe")

    def test_empty_literal_address_counts_as_no_address(self):
        """Regression test: forms and the REST API submit `""` for an empty Address field."""
        forwarder = DNSForwarder(name="Corp resolver", ip_address=self.ip_address, address="")
        forwarder.validated_save()
        self.assertIsNone(DNSForwarder.objects.get(pk=forwarder.pk).address)
        with self.assertRaises(ValidationError):
            DNSForwarder(name="Nothing", address="").full_clean()

    def test_requires_exactly_one_address(self):
        for kwargs in ({}, {"ip_address": self.ip_address, "address": "192.0.2.53"}):
            with self.subTest(fields=sorted(kwargs)), self.assertRaises(ValidationError):
                DNSForwarder(name="Invalid", **kwargs).full_clean()

    def test_address_and_port_may_repeat_but_name_may_not(self):
        DNSForwarder(name="IPAM", ip_address=self.ip_address).validated_save()
        DNSForwarder(name="Literal", address="192.0.2.53").validated_save()
        DNSForwarder(name="Literal again", address="192.0.2.53").validated_save()
        other_namespace = Namespace.objects.create(name="Other")
        Prefix.objects.create(
            prefix="192.0.2.0/24", namespace=other_namespace, type="Pool", status=Status.objects.get(name="Active")
        )
        overlapping = IPAddress.objects.create(
            address="192.0.2.53/32", namespace=other_namespace, status=Status.objects.get(name="Active")
        )
        DNSForwarder(name="Other namespace", ip_address=overlapping).validated_save()
        self.assertEqual(DNSForwarder.objects.filter(port=53).count(), 4)

        with self.assertRaises(ValidationError):
            DNSForwarder(name="Literal", address="192.0.2.99").full_clean()

    def test_port_range(self):
        for port in (0, 65536):
            with self.subTest(port=port), self.assertRaises(ValidationError):
                DNSForwarder(name="Invalid", address="192.0.2.1", port=port).full_clean()


class DNSForwardingRuleTestCase(TestCase):
    """Test the DNSForwardingRule model."""

    def test_rule_with_forwarders(self):
        forwarder = DNSForwarder.objects.create(name="Corp resolver", address="192.0.2.53")
        rule = DNSForwardingRule(name="corp.example.com")
        rule.validated_save()
        rule.forwarders.add(forwarder)

        self.assertEqual(rule.dns_view, DNSView.objects.get(name="Default"))
        self.assertEqual(str(rule), "corp.example.com (Default)")
        self.assertQuerySetEqual(forwarder.forwarding_rules.all(), [rule])

    def test_root_forwards_all_queries(self):
        DNSForwardingRule(name=".").validated_save()

    def test_rejects_empty_labels(self):
        with self.assertRaises(ValidationError):
            DNSForwardingRule(name="corp..example.com").full_clean()

    def test_name_is_unique_per_view_ignoring_case(self):
        DNSForwardingRule(name="corp.example.com").validated_save()
        for name in ("corp.example.com", "CORP.example.com"):
            with self.subTest(name=name), self.assertRaises(ValidationError) as context:
                DNSForwardingRule(name=name).validated_save()
            self.assertIn("ignoring letter case", str(context.exception.message_dict["name"]))
        DNSForwardingRule(name="CORP.example.com", dns_view=DNSView.objects.create(name="Other")).validated_save()

    def test_database_rejects_a_name_differing_only_by_case(self):
        DNSForwardingRule(name="corp.example.com").validated_save()
        with self.assertRaises(IntegrityError), transaction.atomic():
            DNSForwardingRule.objects.create(name="CORP.example.com")
