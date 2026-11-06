"""Tests for DNS zone name collision detection, reporting, and the migration check."""

import importlib
from io import StringIO
from types import SimpleNamespace
from unittest import mock, skipUnless

from django.core.management import CommandError, call_command
from django.db import connection
from nautobot.apps.testing import TestCase

from nautobot_dns_models.models import DNSView, DNSZone, NSRecord
from nautobot_dns_models.utils import format_dns_zone_name_collisions, get_dns_zone_name_collisions

migration_0013 = importlib.import_module("nautobot_dns_models.migrations.0013_dnszone_name_case_insensitive_unique")

COMMAND_NAME = "check_dns_zone_name_collisions"


def _fake_zone(name, pk, view_name="Default"):
    return SimpleNamespace(name=name, pk=pk, dns_view=SimpleNamespace(name=view_name))


class GetDNSZoneNameCollisionsTestCase(TestCase):
    """Test get_dns_zone_name_collisions() and the copy of it in migration 0013."""

    detectors = {
        "utils": get_dns_zone_name_collisions,
        "migration_0013": migration_0013.get_dns_zone_name_collisions,
    }

    def test_no_collisions(self):
        """Distinct names, and the same name in different views, are not collisions."""
        other_view = DNSView.objects.create(name="Other View")
        DNSZone.objects.create(name="example.com")
        DNSZone.objects.create(name="example.org")
        DNSZone.objects.create(name="Example.com", dns_view=other_view)

        for label, detector in self.detectors.items():
            with self.subTest(detector=label):
                self.assertEqual(detector(DNSZone), [])

    # MySQL's default case-insensitive collation already rejected case variants under the old unique_together,
    # and its DDL commits implicitly, so the constraint cannot be dropped inside a test transaction there.
    @skipUnless(connection.vendor == "postgresql", "Requires transactional DDL to drop the constraint within a test.")
    def test_collisions_grouped_by_view_and_name(self):
        """Zones differing only by case are grouped per view, with groups ordered by view name."""
        with connection.schema_editor() as schema_editor:
            schema_editor.remove_constraint(DNSZone, DNSZone._meta.constraints[0])
        other_view = DNSView.objects.create(name="Other View")
        lower = DNSZone.objects.create(name="example.com")
        upper = DNSZone.objects.create(name="EXAMPLE.com")
        other_lower = DNSZone.objects.create(name="example.com", dns_view=other_view)
        other_mixed = DNSZone.objects.create(name="Example.com", dns_view=other_view)
        DNSZone.objects.create(name="example.org")

        for label, detector in self.detectors.items():
            with self.subTest(detector=label):
                collisions = detector(DNSZone)
                self.assertEqual([set(group) for group in collisions], [{upper, lower}, {other_mixed, other_lower}])


class FormatDNSZoneNameCollisionsTestCase(TestCase):
    """Test format_dns_zone_name_collisions()."""

    def setUp(self):
        self.collisions = [
            [_fake_zone("Example.com", 1), _fake_zone("example.com", 2)],
            [_fake_zone("Example.org", 3, "Internal"), _fake_zone("example.org", 4, "Internal")],
        ]

    def test_lists_every_group(self):
        self.assertEqual(
            format_dns_zone_name_collisions(self.collisions),
            "\n".join(
                [
                    "Found 2 group(s) of DNS zones whose names differ only by letter case within the same DNS view.",
                    '    View "Default": "Example.com" (ID 1), "example.com" (ID 2)',
                    '    View "Internal": "Example.org" (ID 3), "example.org" (ID 4)',
                ]
            ),
        )

    def test_limit_summarizes_remaining_groups(self):
        message = format_dns_zone_name_collisions(self.collisions, limit=1)
        self.assertIn('View "Default"', message)
        self.assertNotIn('View "Internal"', message)
        self.assertTrue(message.endswith("    ...and 1 more."))

    def test_record_counts(self):
        message = format_dns_zone_name_collisions(self.collisions[:1], record_counts={1: 3})
        self.assertIn('"Example.com" (ID 1, 3 record(s)), "example.com" (ID 2, 0 record(s))', message)


class CheckZoneCollisionsCommandTestCase(TestCase):
    """Test the check_dns_zone_name_collisions management command."""

    def test_no_collisions(self):
        DNSZone.objects.create(name="example.com")
        stdout = StringIO()

        call_command(COMMAND_NAME, stdout=stdout)

        self.assertIn("No DNS zone name collisions found.", stdout.getvalue())

    def test_collisions_reported_with_record_counts(self):
        zone = DNSZone.objects.create(name="example.com")
        NSRecord.objects.create(name="@", server="ns1.example.com", zone=zone)
        NSRecord.objects.create(name="@", server="ns2.example.com", zone=zone)
        stdout = StringIO()

        with mock.patch(
            "nautobot_dns_models.management.commands.check_dns_zone_name_collisions.get_dns_zone_name_collisions",
            return_value=[[zone, _fake_zone("EXAMPLE.com", "00000000-0000-0000-0000-000000000000")]],
        ):
            with self.assertRaises(CommandError):
                call_command(COMMAND_NAME, stdout=stdout)

        self.assertIn(f'"example.com" (ID {zone.pk}, 2 record(s))', stdout.getvalue())
        self.assertIn('"EXAMPLE.com" (ID 00000000-0000-0000-0000-000000000000, 0 record(s))', stdout.getvalue())


class MigrationCollisionCheckTestCase(TestCase):
    """Test the collision check run by migration 0013 before the constraint is added."""

    def setUp(self):
        self.apps = mock.Mock()
        self.apps.get_model.return_value = DNSZone

    def test_passes_without_collisions(self):
        with mock.patch.object(migration_0013, "get_dns_zone_name_collisions", return_value=[]):
            migration_0013.check_for_dns_zone_name_collisions(self.apps, None)

    def test_aborts_and_lists_capped_collisions(self):
        collisions = [
            [_fake_zone(f"Zone{index}.example", index * 2), _fake_zone(f"zone{index}.example", index * 2 + 1)]
            for index in range(migration_0013.COLLISION_REPORT_LIMIT + 5)
        ]

        with mock.patch.object(migration_0013, "get_dns_zone_name_collisions", return_value=collisions):
            with self.assertRaises(migration_0013.DNSZoneNameCollisionError) as context:
                migration_0013.check_for_dns_zone_name_collisions(self.apps, None)

        message = str(context.exception)
        self.assertTrue(message.startswith("Migration aborted:"))
        self.assertIn('"Zone0.example" (ID 0), "zone0.example" (ID 1)', message)
        self.assertNotIn(f'"Zone{migration_0013.COLLISION_REPORT_LIMIT}.example"', message)
        self.assertIn("...and 5 more.", message)
        self.assertIn(f"nautobot-server {COMMAND_NAME}", message)
