"""Tests for nautobot_dns_models Form Classes."""

from django.test import TestCase
from nautobot.extras.models.statuses import Status
from nautobot.ipam.models import IPAddress, Namespace, Prefix

from nautobot_dns_models import forms
from nautobot_dns_models.models import DNSZoneModel


class DNSZoneModelTest(TestCase):
    """Test DnsZoneModel forms."""

    def test_specifying_all_fields_success(self):
        form = forms.DNSZoneModelForm(
            data={
                "name": "Development",
                "description": "Development Testing",
                "ttl": 1010101,
                "filename": "development.zone",
                "soa_mname": "ns1.example.com",
                "soa_rname": "admin@example.com",
                "soa_refresh": 10800,
                "soa_retry": 3600,
                "soa_expire": 604800,
                "soa_serial": 202,
                "soa_minimum": 3600,
            }
        )
        self.assertTrue(form.is_valid())
        self.assertTrue(form.save())

    def test_specifying_only_required_success(self):
        form = forms.DNSZoneModelForm(
            data={
                "name": "Development",
                "ttl": 1010101,
                "filename": "development.zone",
                "soa_mname": "ns1.example.com",
                "soa_rname": "admin@example.com",
                "soa_refresh": 10800,
                "soa_retry": 3600,
                "soa_expire": 604800,
                "soa_serial": 202,
                "soa_minimum": 3600,
            }
        )
        self.assertTrue(form.is_valid())
        self.assertTrue(form.save())

    def test_validate_name_dnszonemodel_is_required(self):
        form = forms.DNSZoneModelForm(data={"ttl": "1010101"})
        self.assertFalse(form.is_valid())
        self.assertIn("This field is required.", form.errors["name"])


class NSRecordModelFormTestCase(TestCase):
    """Test NSRecordModel forms."""

    form_class = forms.NSRecordModelForm

    @classmethod
    def setUpTestData(cls):
        cls.dns_zone = DNSZoneModel.objects.create(name="example.com")

    def test_specifying_all_fields_success(self):
        data = {
            "name": "ns-record",
            "server": "ns-record-server",
            "description": "Development Testing",
            "ttl": 3600,
            "zone": self.dns_zone,
        }
        form = self.form_class(data)
        self.assertTrue(form.is_valid())
        self.assertTrue(form.save())

    def test_specifying_only_required_success(self):
        data = {
            "name": "ns-record",
            "server": "ns-record-server",
            "ttl": 3600,
            "zone": self.dns_zone,
        }
        form = self.form_class(data)
        self.assertTrue(form.is_valid())
        self.assertTrue(form.save())

    def test_zone_is_required(self):
        data = {
            "name": "ns-record",
            "server": "ns-record-server",
        }
        form = self.form_class(data)
        self.assertFalse(form.is_valid())
        self.assertTrue(form.errors)
        self.assertIn("This field is required.", form.errors["zone"])


class ARecordModelFormTestCase(TestCase):
    """Test ARecordModel forms."""

    form_class = forms.ARecordModelForm

    @classmethod
    def setUpTestData(cls):
        cls.dns_zone = DNSZoneModel.objects.create(name="example.com")
        status = Status.objects.get(name="Active")
        namespace = Namespace.objects.get(name="Global")
        Prefix.objects.create(prefix="10.0.0.0/24", namespace=namespace, type="Pool", status=status)
        cls.ip_address = IPAddress.objects.create(address="10.0.0.1/32", namespace=namespace, status=status)

    def test_specifying_only_required_success(self):
        data = {
            "name": "a-record",
            "address": self.ip_address,
            "ttl": 3600,
            "zone": self.dns_zone,
        }
        form = self.form_class(data)
        self.assertTrue(form.is_valid())
        self.assertTrue(form.save())

    def test_specifying_all_fields_success(self):
        data = {
            "name": "a-record",
            "address": self.ip_address,
            "ttl": 3600,
            "zone": self.dns_zone,
            "comment": "example-comment",
            "description": "this is Gerasimo's description",
        }
        form = self.form_class(data)
        self.assertTrue(form.is_valid())
        self.assertTrue(form.save())

    def test_ip_address_obj_is_required(self):
        data = {
            "name": "a-record",
            "address": "10.10.10.0/32",
            "ttl": 3600,
            "zone": self.dns_zone,
        }
        form = self.form_class(data)
        self.assertFalse(form.is_valid())
        self.assertTrue(form.errors)
        self.assertIn("not a valid UUID.", form.errors["address"][0])


class AAAARecordModelFormTestCase(TestCase):
    """Test AAAARecordModel forms."""

    form_class = forms.AAAARecordModelForm

    @classmethod
    def setUpTestData(cls):
        cls.dns_zone = DNSZoneModel.objects.create(name="example.com")
        status = Status.objects.get(name="Active")
        namespace = Namespace.objects.get(name="Global")
        Prefix.objects.create(prefix="2001:db8:abcd:12::/64", namespace=namespace, type="Pool", status=status)
        cls.ip_address = IPAddress.objects.create(address="2001:db8:abcd:12::1/128", namespace=namespace, status=status)

    def test_specifying_only_required_success(self):
        data = {
            "name": "aaaa-record",
            "address": self.ip_address,
            "ttl": 3600,
            "zone": self.dns_zone,
        }
        form = self.form_class(data)
        self.assertTrue(form.is_valid())
        self.assertTrue(form.save())

    def test_specifying_all_fields_success(self):
        data = {
            "name": "aaaa-record",
            "address": self.ip_address,
            "ttl": 3600,
            "zone": self.dns_zone,
            "comment": "example-comment",
            "description": "this is Gerasimo's description",
        }
        form = self.form_class(data)
        self.assertTrue(form.is_valid())
        self.assertTrue(form.save())

    def test_ip_address_obj_is_required(self):
        data = {
            "name": "aaaa-record",
            "address": "10.10.10.0/32",
            "ttl": 3600,
            "zone": self.dns_zone,
        }
        form = self.form_class(data)
        self.assertFalse(form.is_valid())
        self.assertTrue(form.errors)


class CNAMERecordModelFormTestCase(TestCase):
    """Test CNAMERecordModel forms."""

    form_class = forms.CNAMERecordModelForm

    @classmethod
    def setUpTestData(cls):
        cls.dns_zone = DNSZoneModel.objects.create(name="example.com")

    def test_specifying_only_required_success(self):
        data = {
            "name": "cname-record",
            "alias": "cname-alias",
            "ttl": 3600,
            "zone": self.dns_zone,
        }
        form = self.form_class(data)
        self.assertTrue(form.is_valid())
        self.assertTrue(form.save())

    def test_specifying_all_fields_success(self):
        data = {
            "name": "cname-record",
            "alias": "cname-alias",
            "ttl": 3600,
            "zone": self.dns_zone,
            "description": "this is a cname description",
        }
        form = self.form_class(data)
        self.assertTrue(form.is_valid())
        self.assertTrue(form.save())


class MXRecordModelFormTestCase(TestCase):
    """Test MXRecordModel forms."""

    form_class = forms.MXRecordModelForm

    @classmethod
    def setUpTestData(cls):
        cls.dns_zone = DNSZoneModel.objects.create(name="example.com")

    def test_specifying_only_required_success(self):
        data = {
            "name": "mx-record",
            "preference": 10,
            "mail_server": "mail-server.com",
            "ttl": 3600,
            "zone": self.dns_zone,
        }
        form = self.form_class(data)
        self.assertTrue(form.is_valid())
        self.assertTrue(form.save())

    def test_specifying_all_fields_success(self):
        data = {
            "name": "mx-record",
            "preference": 10,
            "mail_server": "mail-server.com",
            "ttl": 3600,
            "zone": self.dns_zone,
            "description": "this is a boring description",
        }
        form = self.form_class(data)
        self.assertTrue(form.is_valid())
        self.assertTrue(form.save())


class TXTRecordModelFormTestCase(TestCase):
    """Test TXTRecordModel forms."""

    form_class = forms.TXTRecordModelForm

    @classmethod
    def setUpTestData(cls):
        cls.dns_zone = DNSZoneModel.objects.create(name="example.com")

    def test_specifying_only_required_success(self):
        data = {
            "name": "txt-record",
            "text": "spf record",
            "ttl": 3600,
            "zone": self.dns_zone,
        }
        form = self.form_class(data)
        self.assertTrue(form.is_valid())
        self.assertTrue(form.save())

    def test_specifying_all_fields_success(self):
        data = {
            "name": "txt-record",
            "text": "spf record",
            "ttl": 3600,
            "zone": self.dns_zone,
            "description": "this is a boring description",
        }
        form = self.form_class(data)
        self.assertTrue(form.is_valid())
        self.assertTrue(form.save())


class PTRRecordModelFormTestCase(TestCase):
    """Test PTRRecordModel forms."""

    form_class = forms.PTRRecordModelForm

    @classmethod
    def setUpTestData(cls):
        cls.dns_zone = DNSZoneModel.objects.create(name="example.com")

    def test_specifying_only_required_success(self):
        data = {
            "name": "ptr-record",
            "ptrdname": "ptr-record",
            "ttl": 3600,
            "zone": self.dns_zone,
        }
        form = self.form_class(data)
        self.assertTrue(form.is_valid())
        self.assertTrue(form.save())

    def test_specifying_all_fields_success(self):
        data = {
            "name": "ptr-record",
            "ptrdname": "ptr-record",
            "ttl": 3600,
            "comment": "example-comment",
            "zone": self.dns_zone,
            "description": "this is a boring description",
        }
        form = self.form_class(data)
        self.assertTrue(form.is_valid())
        self.assertTrue(form.save())
