"""Test DnsZoneModel."""

from django.test import TestCase
from nautobot.extras.models.statuses import Status
from nautobot.ipam.models import IPAddress, Namespace, Prefix

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


class DNSZoneModelTest(TestCase):
    """Test DnsZoneModel."""

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
