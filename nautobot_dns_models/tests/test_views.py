"""Unit tests for views."""

from django.contrib.auth import get_user_model
from nautobot.apps.testing import ViewTestCases
from nautobot.extras.models import Status
from nautobot.ipam.models import IPAddress, Namespace, Prefix

from nautobot_dns_models.models import (
    AAAARecord,
    ARecord,
    CNAMERecord,
    DNSZone,
    MXRecord,
    NSRecord,
    PTRRecord,
    SRVRecord,
    TXTRecord,
)

User = get_user_model()


class DnsZoneViewTest(ViewTestCases.PrimaryObjectViewTestCase):
    # pylint: disable=too-many-ancestors
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


class NSRecordViewTest(ViewTestCases.PrimaryObjectViewTestCase):
    # pylint: disable=too-many-ancestors
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
        }

        cls.csv_data = (
            "name,server,zone, ttl",
            f"Test 3,server 3,{zone.name}, 3600",
        )

        cls.bulk_edit_data = {"description": "Bulk edit views"}


class ARecordViewTest(ViewTestCases.PrimaryObjectViewTestCase):
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
        ip_addresses = (
            IPAddress.objects.create(address="10.0.0.1/32", namespace=namespace, status=status),
            IPAddress.objects.create(address="10.0.0.2/32", namespace=namespace, status=status),
            IPAddress.objects.create(address="10.0.0.3/32", namespace=namespace, status=status),
        )

        ARecord.objects.create(
            name="primary",
            address=ip_addresses[0],
            zone=zone,
        )
        ARecord.objects.create(
            name="primary",
            address=ip_addresses[1],
            zone=zone,
        )
        ARecord.objects.create(
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


class AAAARecordViewTest(ViewTestCases.PrimaryObjectViewTestCase):
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
        ip_addresses = (
            IPAddress.objects.create(address="2001:db8:abcd:12::1/128", namespace=namespace, status=status),
            IPAddress.objects.create(address="2001:db8:abcd:12::2/128", namespace=namespace, status=status),
            IPAddress.objects.create(address="2001:db8:abcd:12::3/128", namespace=namespace, status=status),
        )

        AAAARecord.objects.create(
            name="primary",
            address=ip_addresses[0],
            zone=zone,
        )
        AAAARecord.objects.create(
            name="primary",
            address=ip_addresses[1],
            zone=zone,
        )
        AAAARecord.objects.create(
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


class CNAMERecordViewTest(ViewTestCases.PrimaryObjectViewTestCase):
    # pylint: disable=too-many-ancestors
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
        }

        cls.csv_data = (
            "name,alias,zone",
            f"Test 3,test2.example.com,{zone.name}",
        )

        cls.bulk_edit_data = {"description": "Bulk edit views"}


class MXRecordViewTest(ViewTestCases.PrimaryObjectViewTestCase):
    # pylint: disable=too-many-ancestors
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
        }

        cls.csv_data = (
            "name,mail_server,zone",
            f"Test 3,test_mail2.example.com,{zone.name}",
        )

        cls.bulk_edit_data = {"description": "Bulk edit views"}


class TXTRecordViewTest(ViewTestCases.PrimaryObjectViewTestCase):
    # pylint: disable=too-many-ancestors
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
        }

        cls.csv_data = (
            "name,text,zone",
            f"Test 3,test-text,{zone.name}",
        )

        cls.bulk_edit_data = {"description": "Bulk edit views"}


class PTRRecordViewTest(ViewTestCases.PrimaryObjectViewTestCase):
    # pylint: disable=too-many-ancestors
    """Test the PTRRecord views."""

    model = PTRRecord

    @classmethod
    def setUpTestData(cls):
        zone = DNSZone.objects.create(
            name="example.com",
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

        cls.bulk_edit_data = {"description": "Bulk edit views"}


class SRVRecordViewTest(ViewTestCases.PrimaryObjectViewTestCase):
    # pylint: disable=too-many-ancestors
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
        }

        cls.csv_data = (
            "name,priority,weight,port,target,zone",
            f"_ldap._tcp,20,10,389,ldap.example.com,{zone.name}",
        )

        cls.bulk_edit_data = {"description": "Bulk edit views"}
