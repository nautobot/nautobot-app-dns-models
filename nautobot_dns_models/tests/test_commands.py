"""Test management commands."""

from io import StringIO

from django.core.management import call_command
from nautobot.apps.testing import TestCase
from nautobot.extras.models import Status
from nautobot.ipam.models import IPAddress, Namespace, Prefix

from nautobot_dns_models.models import DNSZone, PTRRecord


class LinkPTRRecordsToIPAddressesTestCase(TestCase):
    """Test the link_ptr_records_to_ip_addresses management command."""

    @classmethod
    def setUpTestData(cls):
        status = Status.objects.get(name="Active")
        global_namespace = Namespace.objects.get(name="Global")
        other_namespace = Namespace.objects.create(name="Other")
        for namespace in (global_namespace, other_namespace):
            Prefix.objects.create(prefix="10.0.0.0/24", namespace=namespace, type="Pool", status=status)
        Prefix.objects.create(prefix="2001:db8::/32", namespace=global_namespace, type="Pool", status=status)

        cls.ip_1 = IPAddress.objects.create(address="10.0.0.1/32", namespace=global_namespace, status=status)
        cls.ip_2 = IPAddress.objects.create(address="10.0.0.2/32", namespace=global_namespace, status=status)
        cls.ip_3_global = IPAddress.objects.create(address="10.0.0.3/32", namespace=global_namespace, status=status)
        cls.ip_3_other = IPAddress.objects.create(address="10.0.0.3/32", namespace=other_namespace, status=status)
        cls.ipv6 = IPAddress.objects.create(address="2001:db8::1/128", namespace=global_namespace, status=status)

        cls.reverse_zone = DNSZone.objects.create(name="0.0.10.in-addr.arpa")
        cls.reverse_v6_zone = DNSZone.objects.create(name="8.b.d.0.1.0.0.2.ip6.arpa")
        cls.forward_zone = DNSZone.objects.create(name="example.com")

        cls.ptr_1 = PTRRecord.objects.create(name="1", ptrdname="host1.example.com", zone=cls.reverse_zone)
        cls.ptr_3 = PTRRecord.objects.create(name="3", ptrdname="host3.example.com", zone=cls.reverse_zone)
        cls.ptr_9 = PTRRecord.objects.create(name="9", ptrdname="host9.example.com", zone=cls.reverse_zone)
        cls.ptr_bad = PTRRecord.objects.create(name="host", ptrdname="host.example.com", zone=cls.forward_zone)
        cls.ptr_v6 = PTRRecord.objects.create(
            name="1.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0",
            ptrdname="v6host.example.com",
            zone=cls.reverse_v6_zone,
        )
        # Linked to the "wrong" IP; only reconsidered with --relink.
        cls.ptr_2 = PTRRecord.objects.create(
            name="2", ptrdname="host2.example.com", zone=cls.reverse_zone, ip_address=cls.ip_1
        )

    def _call(self, *args):
        out = StringIO()
        call_command("link_ptr_records_to_ip_addresses", *args, stdout=out)
        return out.getvalue()

    def _refresh(self):
        for ptr_record in (self.ptr_1, self.ptr_2, self.ptr_3, self.ptr_9, self.ptr_bad, self.ptr_v6):
            ptr_record.refresh_from_db()

    def test_dry_run_reports_and_changes_nothing(self):
        output = self._call()
        self._refresh()

        self.assertIsNone(self.ptr_1.ip_address)
        self.assertIsNone(self.ptr_v6.ip_address)
        self.assertIn("1.0.0.10.in-addr.arpa (host1.example.com) -> 10.0.0.1/32 [Global]", output)
        self.assertIn("2001:db8::1/128", output)
        self.assertIn("3.0.0.10.in-addr.arpa (host3.example.com) -> 10.0.0.3/32 [Global], 10.0.0.3/32 [Other]", output)
        self.assertIn("9.0.0.10.in-addr.arpa (host9.example.com) -> 10.0.0.9", output)
        self.assertIn("host.example.com (host.example.com)", output)
        self.assertIn("Summary: 2 to link, 1 ambiguous, 1 without a match, 1 unparseable.", output)
        self.assertIn("Dry run", output)

    def test_commit_links_unambiguous_matches(self):
        output = self._call("--commit")
        self._refresh()

        self.assertEqual(self.ptr_1.ip_address, self.ip_1)
        self.assertEqual(self.ptr_v6.ip_address, self.ipv6)
        self.assertIsNone(self.ptr_3.ip_address)
        self.assertIsNone(self.ptr_9.ip_address)
        self.assertIsNone(self.ptr_bad.ip_address)
        self.assertEqual(self.ptr_2.ip_address, self.ip_1)
        self.assertIn("Linked 2 PTR record(s).", output)

    def test_relink_corrects_existing_links(self):
        self._call("--commit", "--relink")
        self._refresh()

        self.assertEqual(self.ptr_2.ip_address, self.ip_2)
        self.assertEqual(self.ptr_1.ip_address, self.ip_1)

    def test_zone_limits_scope(self):
        output = self._call("--commit", "--zone", self.reverse_v6_zone.name)
        self._refresh()

        self.assertEqual(self.ptr_v6.ip_address, self.ipv6)
        self.assertIsNone(self.ptr_1.ip_address)
        self.assertIn("Summary: 1 to link, 0 ambiguous, 0 without a match, 0 unparseable.", output)
