"""Tests for nautobot_dns_models Form Classes."""

from django.test import TestCase
from nautobot.extras.models.statuses import Status
from nautobot.ipam.models import IPAddress, Namespace, Prefix

from nautobot_dns_models import forms
from nautobot_dns_models.models import DNSZoneModel


class NSRecordModelFormTestCase(TestCase):
    """Test NSRecordModel forms."""

    form_class = forms.NSRecordModelForm

    @classmethod
    def setUpTestData(cls):
        cls.dns_zone = DNSZoneModel.objects.create(name="example.com", slug="example_com")

    def test_specifying_all_fields_success(self):
        data = {
            "name": "ns-record",
            "slug": "ns-record",
            "server": "ns-record-server",
            "description": "Development Testing",
            "zone": self.dns_zone,
        }
        form = self.form_class(data)
        self.assertTrue(form.is_valid())
        self.assertTrue(form.save())

    def test_specifying_only_required_success(self):
        data = {
            "name": "ns-record",
            "slug": "ns-record",
            "server": "ns-record-server",
            "zone": self.dns_zone,
        }
        form = self.form_class(data)
        self.assertTrue(form.is_valid())
        self.assertTrue(form.save())

    def test_zone_is_required(self):
        data = {
            "name": "ns-record",
            "slug": "ns-record",
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
        cls.dns_zone = DNSZoneModel.objects.create(name="example.com", slug="example_com")
        status = Status.objects.get(name="Active")
        namespace = Namespace.objects.get(name="Global")
        Prefix.objects.create(prefix="10.0.0.0/24", namespace=namespace, type="Pool", status=status)
        cls.ip_address = IPAddress.objects.create(address="10.0.0.1/32", namespace=namespace, status=status)

    def test_specifying_only_required_success(self):
        data = {
            "name": "a-record",
            "slug": "a-record",
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
            "slug": "a-record",
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
            "slug": "a-record",
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
        cls.dns_zone = DNSZoneModel.objects.create(name="example.com", slug="example_com")
        status = Status.objects.get(name="Active")
        namespace = Namespace.objects.get(name="Global")
        Prefix.objects.create(prefix="2001:db8:abcd:12::/64", namespace=namespace, type="Pool", status=status)
        cls.ip_address = IPAddress.objects.create(address="2001:db8:abcd:12::1/128", namespace=namespace, status=status)

    def test_specifying_only_required_success(self):
        data = {
            "name": "aaaa-record",
            "slug": "aaaa-record",
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
            "slug": "aaaa-record",
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
            "slug": "aaaa-record",
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
        cls.dns_zone = DNSZoneModel.objects.create(name="example.com", slug="example_com")

    def test_specifying_only_required_success(self):
        data = {
            "name": "cname-record",
            "slug": "cname-record",
            "alias": "cname-alias",
            "zone": self.dns_zone,
        }
        form = self.form_class(data)
        self.assertTrue(form.is_valid())
        self.assertTrue(form.save())

    def test_specifying_all_fields_success(self):
        data = {
            "name": "cname-record",
            "slug": "cname-record",
            "alias": "cname-alias",
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
        cls.dns_zone = DNSZoneModel.objects.create(name="example.com", slug="example_com")

    def test_specifying_only_required_success(self):
        data = {
            "name": "mx-record",
            "slug": "mx-record",
            "preference": 10,
            "mail_server": "mail-server.com",
            "zone": self.dns_zone,
        }
        form = self.form_class(data)
        self.assertTrue(form.is_valid())
        self.assertTrue(form.save())

    def test_specifying_all_fields_success(self):
        data = {
            "name": "mx-record",
            "slug": "mx-record",
            "preference": 10,
            "mail_server": "mail-server.com",
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
        cls.dns_zone = DNSZoneModel.objects.create(name="example.com", slug="example_com")

    def test_specifying_only_required_success(self):
        data = {
            "name": "txt-record",
            "slug": "txt-record",
            "text": "spf record",
            "zone": self.dns_zone,
        }
        form = self.form_class(data)
        self.assertTrue(form.is_valid())
        self.assertTrue(form.save())

    def test_specifying_all_fields_success(self):
        data = {
            "name": "txt-record",
            "slug": "txt-record",
            "text": "spf record",
            "zone": self.dns_zone,
            "description": "this is a boring description",
        }
        form = self.form_class(data)
        self.assertTrue(form.is_valid())
        self.assertTrue(form.save())
