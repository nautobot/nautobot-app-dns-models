"""Tests for nautobot_dns_models Form Classes."""

from django.test import TestCase
from nautobot.extras.models.statuses import Status
from nautobot.ipam.models import IPAddress, Namespace, Prefix

from nautobot_dns_models import forms
from nautobot_dns_models.models import DNSView, DNSZone


class DNSViewFormTestCase(TestCase):
    """Test DNSView forms."""

    form_class = forms.DNSViewForm

    @classmethod
    def setUpTestData(cls):
        active_status = Status.objects.get(name="Active")
        namespace = Namespace.objects.get(name="Global")
        cls.prefix = Prefix.objects.create(prefix="10.0.0.0/24", namespace=namespace, status=active_status)

    def test_specifying_all_fields_success(self):
        form = self.form_class(
            data={"name": "Test View", "description": "Test Description", "prefixes": [self.prefix.pk]}
        )
        self.assertTrue(form.is_valid())
        self.assertTrue(form.save())

    def test_specifying_only_required_success(self):
        form = self.form_class(data={"name": "Test View"})
        self.assertTrue(form.is_valid())
        self.assertTrue(form.save())

    def test_validate_name_dnsview_is_required(self):
        form = self.form_class(data={"description": "Test Description"})
        self.assertFalse(form.is_valid())
        self.assertIn("This field is required.", form.errors["name"])


class DNSZoneTest(TestCase):
    """Test DNSZone forms."""

    def test_specifying_all_fields_success(self):
        form = forms.DNSZoneForm(
            data={
                "name": "Development",
                "dns_view": DNSView.objects.get(name="Default").id,
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
        form = forms.DNSZoneForm(
            data={
                "name": "Development",
                "dns_view": DNSView.objects.get(name="Default").id,
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

    def test_validate_name_dnszone_is_required(self):
        form = forms.DNSZoneForm(data={"ttl": "1010101"})
        self.assertFalse(form.is_valid())
        self.assertIn("This field is required.", form.errors["name"])


class NSRecordFormTestCase(TestCase):
    """Test NSRecord forms."""

    form_class = forms.NSRecordForm

    @classmethod
    def setUpTestData(cls):
        cls.dns_zone = DNSZone.objects.create(name="example.com")

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


class ARecordFormTestCase(TestCase):
    """Test ARecord forms."""

    form_class = forms.ARecordForm

    @classmethod
    def setUpTestData(cls):
        cls.dns_zone = DNSZone.objects.create(name="example.com")
        status = Status.objects.get(name="Active")
        namespace = Namespace.objects.get(name="Global")
        Prefix.objects.create(prefix="10.0.0.0/24", namespace=namespace, type="Pool", status=status)
        cls.ip_address = IPAddress.objects.create(address="10.0.0.1/32", namespace=namespace, status=status)

    def test_specifying_only_required_success(self):
        data = {
            "name": "a-record",
            "ip_address": self.ip_address,
            "ttl": 3600,
            "zone": self.dns_zone,
        }
        form = self.form_class(data)
        self.assertTrue(form.is_valid())
        self.assertTrue(form.save())

    def test_specifying_all_fields_success(self):
        data = {
            "name": "a-record",
            "ip_address": self.ip_address,
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
            "ip_address": "10.10.10.0/32",
            "ttl": 3600,
            "zone": self.dns_zone,
        }
        form = self.form_class(data)
        self.assertFalse(form.is_valid())
        self.assertTrue(form.errors)
        self.assertIn("not a valid UUID.", form.errors["ip_address"][0])


class AAAARecordFormTestCase(TestCase):
    """Test AAAARecord forms."""

    form_class = forms.AAAARecordForm

    @classmethod
    def setUpTestData(cls):
        cls.dns_zone = DNSZone.objects.create(name="example.com")
        status = Status.objects.get(name="Active")
        namespace = Namespace.objects.get(name="Global")
        Prefix.objects.create(prefix="2001:db8:abcd:12::/64", namespace=namespace, type="Pool", status=status)
        cls.ip_address = IPAddress.objects.create(address="2001:db8:abcd:12::1/128", namespace=namespace, status=status)

    def test_specifying_only_required_success(self):
        data = {
            "name": "aaaa-record",
            "ip_address": self.ip_address,
            "ttl": 3600,
            "zone": self.dns_zone,
        }
        form = self.form_class(data)
        self.assertTrue(form.is_valid())
        self.assertTrue(form.save())

    def test_specifying_all_fields_success(self):
        data = {
            "name": "aaaa-record",
            "ip_address": self.ip_address,
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
            "ip_address": "10.10.10.0/32",
            "ttl": 3600,
            "zone": self.dns_zone,
        }
        form = self.form_class(data)
        self.assertFalse(form.is_valid())
        self.assertTrue(form.errors)


class CNAMERecordFormTestCase(TestCase):
    """Test CNAMERecord forms."""

    form_class = forms.CNAMERecordForm

    @classmethod
    def setUpTestData(cls):
        cls.dns_zone = DNSZone.objects.create(name="example.com")

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


class MXRecordFormTestCase(TestCase):
    """Test MXRecord forms."""

    form_class = forms.MXRecordForm

    @classmethod
    def setUpTestData(cls):
        cls.dns_zone = DNSZone.objects.create(name="example.com")

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


class TXTRecordFormTestCase(TestCase):
    """Test TXTRecord forms."""

    form_class = forms.TXTRecordForm

    @classmethod
    def setUpTestData(cls):
        cls.dns_zone = DNSZone.objects.create(name="example.com")

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


class PTRRecordFormTestCase(TestCase):
    """Test PTRRecord forms."""

    form_class = forms.PTRRecordForm

    @classmethod
    def setUpTestData(cls):
        cls.dns_zone = DNSZone.objects.create(name="example.com")

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


class SRVRecordFormTestCase(TestCase):
    """Test SRVRecord forms."""

    form_class = forms.SRVRecordForm

    @classmethod
    def setUpTestData(cls):
        cls.dns_zone = DNSZone.objects.create(name="example.com")

    def test_specifying_only_required_success(self):
        data = {
            "name": "srv-record",
            "priority": 10,
            "weight": 5,
            "port": 8080,
            "target": "server.example.com",
            "ttl": 3600,
            "zone": self.dns_zone,
        }
        form = self.form_class(data)
        self.assertTrue(form.is_valid())
        self.assertTrue(form.save())

    def test_specifying_all_fields_success(self):
        data = {
            "name": "srv-record",
            "priority": 10,
            "weight": 5,
            "port": 8080,
            "target": "server.example.com",
            "ttl": 3600,
            "zone": self.dns_zone,
            "description": "this is an srv description",
            "comment": "example-comment",
        }
        form = self.form_class(data)
        self.assertTrue(form.is_valid())
        self.assertTrue(form.save())

    def test_validate_priority_range(self):
        data = {
            "name": "srv-record",
            "priority": 65536,  # Invalid priority (max is 65535)
            "weight": 5,
            "port": 8080,
            "target": "server.example.com",
            "ttl": 3600,
            "zone": self.dns_zone,
        }
        form = self.form_class(data)
        self.assertFalse(form.is_valid())
        self.assertIn("Ensure this value is less than or equal to 65535.", form.errors["priority"])

    def test_validate_weight_range(self):
        data = {
            "name": "srv-record",
            "priority": 10,
            "weight": 65536,  # Invalid weight (max is 65535)
            "port": 8080,
            "target": "server.example.com",
            "ttl": 3600,
            "zone": self.dns_zone,
        }
        form = self.form_class(data)
        self.assertFalse(form.is_valid())
        self.assertIn("Ensure this value is less than or equal to 65535.", form.errors["weight"])

    def test_validate_port_range(self):
        data = {
            "name": "srv-record",
            "priority": 10,
            "weight": 5,
            "port": 65536,  # Invalid port (max is 65535)
            "target": "server.example.com",
            "ttl": 3600,
            "zone": self.dns_zone,
        }
        form = self.form_class(data)
        self.assertFalse(form.is_valid())
        self.assertIn("Ensure this value is less than or equal to 65535.", form.errors["port"])

    def test_zone_is_required(self):
        data = {
            "name": "srv-record",
            "priority": 10,
            "weight": 5,
            "port": 8080,
            "target": "server.example.com",
            "ttl": 3600,
        }
        form = self.form_class(data)
        self.assertFalse(form.is_valid())
        self.assertIn("This field is required.", form.errors["zone"])

    def test_validate_negative_values(self):
        data = {
            "name": "srv-record",
            "priority": -1,  # Invalid priority (min is 0)
            "weight": -1,  # Invalid weight (min is 0)
            "port": -1,  # Invalid port (min is 0)
            "target": "server.example.com",
            "ttl": 3600,
            "zone": self.dns_zone,
        }
        form = self.form_class(data)
        self.assertFalse(form.is_valid())
        self.assertIn("Ensure this value is greater than or equal to 0.", form.errors["priority"])
        self.assertIn("Ensure this value is greater than or equal to 0.", form.errors["weight"])
        self.assertIn("Ensure this value is greater than or equal to 0.", form.errors["port"])
