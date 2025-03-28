"""Unit tests for views."""

from django.contrib.auth import get_user_model
from nautobot.apps.testing import ViewTestCases
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
    TXTRecordModel,
)

User = get_user_model()


class DnsZoneModelViewTest(ViewTestCases.PrimaryObjectViewTestCase):
    # pylint: disable=too-many-ancestors
    """Test the DnsZoneModel views."""

    model = DNSZoneModel

    @classmethod
    def setUpTestData(cls):
        DNSZoneModel.objects.create(
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
        DNSZoneModel.objects.create(
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
        DNSZoneModel.objects.create(
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

        cls.form_data = {
            "name": "Test 1",
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
        }

        cls.csv_data = (
            "name, ttl, description, filename, soa_mname, soa_rname, soa_refresh, soa_retry, soa_expire, soa_serial, soa_minimum",
            "Test 3, 3600, Description 3, filename 3, auth-server, admin@example_three.com, 86400, 7200, 3600000, 0, 172800",
        )

        cls.bulk_edit_data = {"description": "Bulk edit views"}


class NSRecordModelViewTest(ViewTestCases.PrimaryObjectViewTestCase):
    # pylint: disable=too-many-ancestors
    """Test the NSRecordModel views."""

    model = NSRecordModel

    @classmethod
    def setUpTestData(cls):
        zone = DNSZoneModel.objects.create(
            name="example_one.com",
        )

        NSRecordModel.objects.create(
            name="primary",
            server="example-server.com.",
            zone=zone,
        )
        NSRecordModel.objects.create(
            name="secondary",
            server="example-server.com.",
            zone=zone,
        )
        NSRecordModel.objects.create(
            name="tertiary",
            server="example-server.com.",
            zone=zone,
        )

        cls.form_data = {
            "name": "test record",
            "server": "test server",
            "zone": zone.pk,
            "ttl": 3600,
        }

        cls.csv_data = (
            "name,server,zone, ttl",
            f"Test 3,server 3,{zone.name}, 3600",
        )

        cls.bulk_edit_data = {"description": "Bulk edit views"}


class ARecordModelViewTest(ViewTestCases.PrimaryObjectViewTestCase):
    # pylint: disable=too-many-ancestors
    """Test the ARecordModel views."""

    model = ARecordModel

    @classmethod
    def setUpTestData(cls):
        zone = DNSZoneModel.objects.create(
            name="example_one.com",
        )
        status = Status.objects.get(name="Active")
        namespace = Namespace.objects.get(name="Global")
        Prefix.objects.create(prefix="10.0.0.0/24", namespace=namespace, type="Pool", status=status)
        ip_addresses = (
            IPAddress.objects.create(address="10.0.0.1/32", namespace=namespace, status=status),
            IPAddress.objects.create(address="10.0.0.2/32", namespace=namespace, status=status),
            IPAddress.objects.create(address="10.0.0.3/32", namespace=namespace, status=status),
        )

        ARecordModel.objects.create(
            name="primary",
            address=ip_addresses[0],
            zone=zone,
        )
        ARecordModel.objects.create(
            name="primary",
            address=ip_addresses[1],
            zone=zone,
        )
        ARecordModel.objects.create(
            name="primary",
            address=ip_addresses[2],
            zone=zone,
        )

        cls.form_data = {
            "name": "test record",
            "address": ip_addresses[0].pk,
            "ttl": 3600,
            "zone": zone.pk,
        }

        cls.csv_data = (
            "name,address,zone",
            f"Test 3,{ip_addresses[0].pk},{zone.name}",
        )

        cls.bulk_edit_data = {"description": "Bulk edit views"}


class AAAARecordModelViewTest(ViewTestCases.PrimaryObjectViewTestCase):
    # pylint: disable=too-many-ancestors
    """Test the AAAARecordModel views."""

    model = AAAARecordModel

    @classmethod
    def setUpTestData(cls):
        zone = DNSZoneModel.objects.create(
            name="example_one.com",
        )
        status = Status.objects.get(name="Active")
        namespace = Namespace.objects.get(name="Global")
        Prefix.objects.create(prefix="2001:db8:abcd:12::/64", namespace=namespace, type="Pool", status=status)
        ip_addresses = (
            IPAddress.objects.create(address="2001:db8:abcd:12::1/128", namespace=namespace, status=status),
            IPAddress.objects.create(address="2001:db8:abcd:12::2/128", namespace=namespace, status=status),
            IPAddress.objects.create(address="2001:db8:abcd:12::3/128", namespace=namespace, status=status),
        )

        AAAARecordModel.objects.create(
            name="primary",
            address=ip_addresses[0],
            zone=zone,
        )
        AAAARecordModel.objects.create(
            name="primary",
            address=ip_addresses[1],
            zone=zone,
        )
        AAAARecordModel.objects.create(
            name="primary",
            address=ip_addresses[2],
            zone=zone,
        )

        cls.form_data = {
            "name": "test record",
            "address": ip_addresses[0].pk,
            "ttl": 3600,
            "zone": zone.pk,
        }

        cls.csv_data = (
            "name,address,zone",
            f"Test 3,{ip_addresses[0].pk},{zone.name}",
        )

        cls.bulk_edit_data = {"description": "Bulk edit views"}


class CNAMERecordModelViewTest(ViewTestCases.PrimaryObjectViewTestCase):
    # pylint: disable=too-many-ancestors
    """Test the CNAMERecordModel views."""

    model = CNAMERecordModel

    @classmethod
    def setUpTestData(cls):
        zone = DNSZoneModel.objects.create(
            name="example.com",
        )

        CNAMERecordModel.objects.create(
            name="www.example.com",
            alias="www.example.com",
            zone=zone,
        )
        CNAMERecordModel.objects.create(
            name="mail.example.com",
            alias="mail.example.com",
            zone=zone,
        )
        CNAMERecordModel.objects.create(
            name="blog.example.com",
            alias="blog.example.com",
            zone=zone,
        )

        cls.form_data = {
            "name": "test record",
            "alias": "test.example.com",
            "ttl": 3600,
            "zone": zone.pk,
        }

        cls.csv_data = (
            "name,alias,zone",
            f"Test 3,test2.example.com,{zone.name}",
        )

        cls.bulk_edit_data = {"description": "Bulk edit views"}


class MXRecordModelViewTest(ViewTestCases.PrimaryObjectViewTestCase):
    # pylint: disable=too-many-ancestors
    """Test the MXRecordModel views."""

    model = MXRecordModel

    @classmethod
    def setUpTestData(cls):
        zone = DNSZoneModel.objects.create(
            name="example.com",
        )

        MXRecordModel.objects.create(
            name="mail-record-01",
            mail_server="mail01.example.com",
            zone=zone,
        )
        MXRecordModel.objects.create(
            name="mail-record-02",
            mail_server="mail02.example.com",
            zone=zone,
        )
        MXRecordModel.objects.create(
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
        }

        cls.csv_data = (
            "name,mail_server,zone",
            f"Test 3,test_mail2.example.com,{zone.name}",
        )

        cls.bulk_edit_data = {"description": "Bulk edit views"}


class TXTRecordModelViewTest(ViewTestCases.PrimaryObjectViewTestCase):
    # pylint: disable=too-many-ancestors
    """Test the TXTRecordModel views."""

    model = TXTRecordModel

    @classmethod
    def setUpTestData(cls):
        zone = DNSZoneModel.objects.create(
            name="example.com",
        )

        TXTRecordModel.objects.create(
            name="txt-record-01",
            text="txt-record-01",
            zone=zone,
        )

        TXTRecordModel.objects.create(
            name="txt-record-02",
            text="txt-record-02",
            zone=zone,
        )
        TXTRecordModel.objects.create(
            name="txt-record-03",
            text="txt-record-03",
            zone=zone,
        )

        cls.form_data = {
            "name": "test record",
            "text": "test-text",
            "ttl": 3600,
            "zone": zone.pk,
        }

        cls.csv_data = (
            "name,text,zone",
            f"Test 3,test-text,{zone.name}",
        )

        cls.bulk_edit_data = {"description": "Bulk edit views"}


class PTRRecordModelViewTest(ViewTestCases.PrimaryObjectViewTestCase):
    # pylint: disable=too-many-ancestors
    """Test the PTRRecordModel views."""

    model = PTRRecordModel

    @classmethod
    def setUpTestData(cls):
        zone = DNSZoneModel.objects.create(
            name="example.com",
        )

        PTRRecordModel.objects.create(
            name="ptr-record-01",
            ptrdname="ptr-record-01",
            zone=zone,
        )
        PTRRecordModel.objects.create(
            name="ptr-record-02",
            ptrdname="ptr-record-02",
            zone=zone,
        )
        PTRRecordModel.objects.create(
            name="ptr-record-03",
            ptrdname="ptr-record-03",
            zone=zone,
        )

        cls.form_data = {
            "name": "test record",
            "ptrdname": "ptr-test-record",
            "ttl": 3600,
            "zone": zone.pk,
        }

        cls.csv_data = (
            "name,ptrdname,zone",
            f"Test 3,ptr-test02-record,{zone.name}",
        )

        cls.bulk_edit_data = {"description": "Bulk edit views", "ttl": 3600}
