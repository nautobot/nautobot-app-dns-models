"""Tests for nautobot_dns_models management commands."""

from io import StringIO

from django.core.management import call_command
from nautobot.apps.testing import TestCase

from nautobot_dns_models.models import DNSForwardingRule, DNSZone, NSRecord


class GenerateTestDataCommandTestCase(TestCase):
    """Test the generate_nautobot_dns_models_test_data command."""

    def _generate(self, *args):
        call_command("generate_nautobot_dns_models_test_data", *args, stdout=StringIO())

    def test_generates_delegations_and_forwarding_rules(self):
        self._generate()

        public = DNSZone.objects.get(name="example.com", dns_view__name="Default")
        self.assertEqual(
            [(delegation.fqdn, delegation.child_zone) for delegation in public.get_delegations()],
            [
                ("apps.example.com", DNSZone.objects.get(name="apps.example.com")),
                ("mail.example.com", None),
            ],
        )
        self.assertEqual(DNSZone.objects.get(name="apps.example.com").parent_zone, public)
        self.assertTrue(DNSForwardingRule.objects.filter(name=".", dns_view__name="Internal").exists())

    def test_is_idempotent_and_flush_recreates_the_same_data(self):
        self._generate()
        counts = (DNSZone.objects.count(), NSRecord.objects.count(), DNSForwardingRule.objects.count())

        self._generate()
        self.assertEqual((DNSZone.objects.count(), NSRecord.objects.count(), DNSForwardingRule.objects.count()), counts)

        self._generate("--flush")
        self.assertEqual((DNSZone.objects.count(), NSRecord.objects.count(), DNSForwardingRule.objects.count()), counts)
