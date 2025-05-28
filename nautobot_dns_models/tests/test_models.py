"""Test DnsZoneModel."""

from django.core.exceptions import ValidationError
from nautobot.apps.testing import ModelTestCases, TestCase
from nautobot.extras.models import Status
from nautobot.ipam.models import IPAddress, Namespace, Prefix

from nautobot_dns_models.models import (
    AAAARecordModel,
    ARecordModel,
    CNAMERecordModel,
    DNSZoneModel,
    MXRecordModel,
    NSRecordModel,
    PTRRecordModel,
    SRVRecordModel,
    TXTRecordModel,
)
from nautobot_dns_models.tests import fixtures


class TestDnsZoneModel(ModelTestCases.BaseModelTestCase):
    """Test DnsZoneModel."""

    model = DNSZoneModel

    @classmethod
    def setUpTestData(cls):
        """Create test data for DnsZoneModel Model."""
        super().setUpTestData()
        # Create 3 objects for the model test cases.
        fixtures.create_dnszonemodel()

    def test_create_dnszonemodel_only_required(self):
        """Create with only required fields, and validate null description and __str__."""
        dnszonemodel = DNSZoneModel.objects.create(name="Development")
        self.assertEqual(dnszonemodel.name, "Development")
        self.assertEqual(dnszonemodel.description, "")
        self.assertEqual(str(dnszonemodel), "Development")

    def test_create_dnszonemodel_all_fields_success(self):
        """Create DnsZoneModel with all fields."""
        dnszonemodel = DNSZoneModel.objects.create(name="Development", description="Development Test")
        self.assertEqual(dnszonemodel.name, "Development")
        self.assertEqual(dnszonemodel.description, "Development Test")

    def test_get_absolute_url(self):
        dns_zone_model = DNSZoneModel(name="example.com")
        self.assertEqual(dns_zone_model.get_absolute_url(), f"/plugins/dns/dns-zones/{dns_zone_model.id}/")


class NSRecordModelTestCase(TestCase):
    """Test the NSRecordModel model."""

    @classmethod
    def setUpTestData(cls):
        cls.dns_zone = DNSZoneModel.objects.create(name="example.com")

    def test_create_nsrecordmodel(self):
        ns_record = NSRecordModel.objects.create(name="primary", server="example-server.com.", zone=self.dns_zone)

        self.assertEqual(ns_record.name, "primary")
        self.assertEqual(ns_record.server, "example-server.com.")
        self.assertEqual(str(ns_record), ns_record.name)

    def test_get_absolute_url(self):
        ns_record = NSRecordModel.objects.create(name="primary", server="example-server.com.", zone=self.dns_zone)
        self.assertEqual(ns_record.get_absolute_url(), f"/plugins/dns/ns-records/{ns_record.id}/")


class ARecordModelTestCase(TestCase):
    """Test the ARecordModel model."""

    @classmethod
    def setUpTestData(cls):
        cls.dns_zone = DNSZoneModel.objects.create(name="example.com")
        status = Status.objects.get(name="Active")
        namespace = Namespace.objects.get(name="Global")
        Prefix.objects.create(prefix="10.0.0.0/24", namespace=namespace, type="Pool", status=status)
        cls.ip_address = IPAddress.objects.create(address="10.0.0.1/32", namespace=namespace, status=status)

    def test_create_arecordmodel(self):
        a_record = ARecordModel.objects.create(name="site.example.com", address=self.ip_address, zone=self.dns_zone)

        self.assertEqual(a_record.name, "site.example.com")
        self.assertEqual(a_record.address, self.ip_address)
        self.assertEqual(a_record.ttl, 3600)
        self.assertEqual(str(a_record), a_record.name)

    def test_get_absolute_url(self):
        a_record = ARecordModel.objects.create(name="site.example.com", address=self.ip_address, zone=self.dns_zone)
        self.assertEqual(a_record.get_absolute_url(), f"/plugins/dns/a-records/{a_record.id}/")


class AAAARecordModelTestCase(TestCase):
    """Test the AAAARecordModel model."""

    @classmethod
    def setUpTestData(cls):
        cls.dns_zone = DNSZoneModel.objects.create(name="example.com")
        status = Status.objects.get(name="Active")
        namespace = Namespace.objects.get(name="Global")
        Prefix.objects.create(prefix="2001:db8:abcd:12::/64", namespace=namespace, type="Pool", status=status)
        cls.ip_address = IPAddress.objects.create(address="2001:db8:abcd:12::1/128", namespace=namespace, status=status)

    def test_create_aaaarecordmodel(self):
        aaaa_record = AAAARecordModel.objects.create(
            name="site.example.com", address=self.ip_address, zone=self.dns_zone
        )

        self.assertEqual(aaaa_record.name, "site.example.com")
        self.assertEqual(aaaa_record.address, self.ip_address)
        self.assertEqual(aaaa_record.ttl, 3600)
        self.assertEqual(str(aaaa_record), aaaa_record.name)

    def test_get_absolute_url(self):
        aaaa_record = AAAARecordModel.objects.create(
            name="site.example.com", address=self.ip_address, zone=self.dns_zone
        )
        self.assertEqual(aaaa_record.get_absolute_url(), f"/plugins/dns/aaaa-records/{aaaa_record.id}/")


class CNAMERecordModelTestCase(TestCase):
    """Test the CNAMERecordModel model."""

    @classmethod
    def setUpTestData(cls):
        cls.dns_zone = DNSZoneModel.objects.create(name="example.com")

    def test_create_cnamerecordmodel(self):
        cname_record = CNAMERecordModel.objects.create(
            name="www.example.com", alias="site.example.com", zone=self.dns_zone
        )

        self.assertEqual(cname_record.name, "www.example.com")
        self.assertEqual(cname_record.alias, "site.example.com")
        self.assertEqual(str(cname_record), cname_record.name)

    def test_get_absolute_url(self):
        cname_record = CNAMERecordModel.objects.create(
            name="www.example.com", alias="site.example.com", zone=self.dns_zone
        )
        self.assertEqual(cname_record.get_absolute_url(), f"/plugins/dns/cname-records/{cname_record.id}/")


class MXRecordModelTestCase(TestCase):
    """Test the MXRecordModel model."""

    @classmethod
    def setUpTestData(cls):
        cls.dns_zone = DNSZoneModel.objects.create(name="example.com")

    def test_create_mxrecordmodel(self):
        mx_record = MXRecordModel.objects.create(name="mail-record", mail_server="mail.example.com", zone=self.dns_zone)

        self.assertEqual(mx_record.name, "mail-record")
        self.assertEqual(mx_record.preference, 10)
        self.assertEqual(mx_record.mail_server, "mail.example.com")
        self.assertEqual(str(mx_record), mx_record.name)

    def test_get_absolute_url(self):
        mx_record = MXRecordModel.objects.create(name="mail-record", mail_server="mail.example.com", zone=self.dns_zone)
        self.assertEqual(mx_record.get_absolute_url(), f"/plugins/dns/mx-records/{mx_record.id}/")


class TXTRecordModelTestCase(TestCase):
    """Test the TXTRecordModel model."""

    @classmethod
    def setUpTestData(cls):
        cls.dns_zone = DNSZoneModel.objects.create(name="example.com")

    def test_create_txtrecordmodel(self):
        txt_record = TXTRecordModel.objects.create(name="txt-record", text="spf-record", zone=self.dns_zone)

        self.assertEqual(txt_record.name, "txt-record")
        self.assertEqual(txt_record.text, "spf-record")
        self.assertEqual(str(txt_record), txt_record.name)

    def test_get_absolute_url(self):
        txt_record = TXTRecordModel.objects.create(name="txt-record", text="spf-record", zone=self.dns_zone)
        self.assertEqual(txt_record.get_absolute_url(), f"/plugins/dns/txt-records/{txt_record.id}/")


class PTRRecordModelTestCase(TestCase):
    """Test the PTRRecordModel model."""

    @classmethod
    def setUpTestData(cls):
        cls.dns_zone = DNSZoneModel.objects.create(name="example.com")

    def test_create_ptrrecordmodel(self):
        ptr_record = PTRRecordModel.objects.create(name="ptr-record", ptrdname="ptr-record", zone=self.dns_zone)

        self.assertEqual(ptr_record.ptrdname, "ptr-record")
        self.assertEqual(str(ptr_record), ptr_record.ptrdname)

    def test_get_absolute_url(self):
        ptr_record = PTRRecordModel.objects.create(ptrdname="ptr-record", zone=self.dns_zone)
        self.assertEqual(ptr_record.get_absolute_url(), f"/plugins/dns/ptr-records/{ptr_record.id}/")


class SRVRecordModelTestCase(TestCase):
    """Test the SRVRecordModel model."""

    @classmethod
    def setUpTestData(cls):
        cls.dns_zone = DNSZoneModel.objects.create(name="example.com")

    def test_create_srvrecordmodel(self):
        srv_record = SRVRecordModel.objects.create(
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

    def test_get_absolute_url(self):
        srv_record = SRVRecordModel.objects.create(
            name="_sip._tcp.example.com", priority=10, weight=5, port=5060, target="sip.example.com", zone=self.dns_zone
        )
        self.assertEqual(srv_record.get_absolute_url(), f"/plugins/dns/srv-records/{srv_record.id}/")


class DNSRecordNameLengthValidationTest(TestCase):
    """Test DNS record name validation rules from RFC 1035 §3.1."""

    @classmethod
    def setUpTestData(cls):
        cls.zone = DNSZoneModel.objects.create(name="example.com")

    def test_valid_record_labels(self):
        """Test that valid record labels are accepted."""
        # Single label
        record = TXTRecordModel(name="www", text="test", zone=self.zone)
        record.full_clean()  # Should not raise

        # Multiple labels
        record = TXTRecordModel(name="www.subdomain", text="test", zone=self.zone)
        record.full_clean()  # Should not raise

        # Maximum length label (63 chars)
        record = TXTRecordModel(name="a" * 63, text="test", zone=self.zone)
        record.full_clean()  # Should not raise

    def test_record_label_too_long(self):
        """Test that record labels exceeding 63 octets are rejected."""
        record = TXTRecordModel(name="a" * 64, text="test", zone=self.zone)
        with self.assertRaises(ValidationError) as context:
            record.full_clean()
        self.assertIn("exceeds maximum length of 63 characters", str(context.exception))

    def test_record_empty_label(self):
        """Test that empty record labels are rejected."""
        record = TXTRecordModel(name="www..subdomain", text="test", zone=self.zone)
        with self.assertRaises(ValidationError) as context:
            record.full_clean()
        self.assertIn("Empty labels are not allowed", str(context.exception))

    def test_record_wire_format_length(self):
        """Test that total wire format length is limited to 255 octets."""
        # Create a zone with a long name to test total length
        zone = DNSZoneModel.objects.create(
            name="x" * 63, filename="x" * 63 + ".zone", soa_mname="ns1." + "x" * 63 + ".", soa_rname="admin@example.com"
        )

        # This should be under 255 octets in wire format:
        # - 1 length octet + 63 octets for label 1
        # - 1 length octet + 63 octets for label 2
        # - 1 length octet + 63 octets for zone name
        # - 1 octet for root label (zero length)
        # Total: (1 + 63) * 3 + 1 = 193
        record = TXTRecordModel(name="x" * 63 + "." + "x" * 63, text="test", zone=zone)
        record.full_clean()  # Should not raise

        # This should exceed 255 octets in wire format
        # - 1 length octet + 63 octets for label 1
        # - 1 length octet + 63 octets for label 2
        # - 1 length octet + 63 octets for label 3
        # - 1 length octet + 63 octets for zone name
        # - 1 octet for root label (zero length)
        # Total: (1 + 63) * 4 + 1 = 257
        record = TXTRecordModel(name="x" * 63 + "." + "x" * 63 + "." + "x" * 63, text="test", zone=zone)
        with self.assertRaises(ValidationError) as context:
            record.full_clean()
        self.assertIn("cannot exceed 255 characters", str(context.exception))


class DNSZoneNameLengthValidationTest(TestCase):
    """Test DNS zone name validation rules from RFC 1035 §3.1.

    Note: We don't test wire format length for zones because the model's CharField
    max_length=200 constraint is stricter than the DNS wire format limit of 255 octets.
    The wire format test is only needed for records, which can have longer names
    when combined with their zone.
    """

    def test_valid_zone_labels(self):
        """Test that valid zone labels are accepted."""
        # Test single label
        zone = DNSZoneModel(name="test1", filename="test1.zone", soa_mname="ns1.test1.", soa_rname="admin@example.com")
        zone.full_clean()  # Should not raise

        # Test multiple labels
        zone = DNSZoneModel(
            name="test2.example.com",
            filename="test2.example.com.zone",
            soa_mname="ns1.test2.example.com.",
            soa_rname="admin@example.com",
        )
        zone.full_clean()  # Should not raise

        # Test maximum length label
        zone = DNSZoneModel(
            name="a" * 63, filename="a" * 63 + ".zone", soa_mname="ns1." + "a" * 63 + ".", soa_rname="admin@example.com"
        )
        zone.full_clean()  # Should not raise

    def test_zone_label_too_long(self):
        """Test that zone labels exceeding 63 octets are rejected."""
        zone = DNSZoneModel(
            name="a" * 64, filename="a" * 64 + ".zone", soa_mname="ns1." + "a" * 64 + ".", soa_rname="admin@example.com"
        )
        with self.assertRaises(ValidationError) as context:
            zone.full_clean()
        self.assertIn("exceeds maximum length of 63 characters", str(context.exception))

    def test_zone_empty_label(self):
        """Test that empty zone labels are rejected."""
        zone = DNSZoneModel(
            name="example..com",
            filename="example..com.zone",
            soa_mname="ns1.example..com.",
            soa_rname="admin@example.com",
        )
        with self.assertRaises(ValidationError) as context:
            zone.full_clean()
        self.assertIn("Empty labels are not allowed", str(context.exception))
