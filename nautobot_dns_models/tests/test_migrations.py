"""Tests that apply migrations to a database populated at an earlier migration state.

These tests are not tagged `migration_test`, because the Nautobot test runner excludes that tag by default
and CI runs only the default `invoke tests`.
"""

import importlib
from unittest import skipUnless

from django.db import IntegrityError, connection, transaction
from django_test_migrations.migrator import Migrator
from nautobot.apps.testing import TransactionTestCase

migration_0013 = importlib.import_module("nautobot_dns_models.migrations.0013_dnszone_name_case_insensitive_unique")


class DNSZoneNameCaseInsensitiveUniqueMigrationTestCase(TransactionTestCase):
    """Test migration 0013, which makes DNS zone names unique within a view regardless of letter case."""

    migrate_from = ("nautobot_dns_models", "0012_txtrecord_rfc1035_text_length")
    migrate_to = ("nautobot_dns_models", "0013_dnszone_name_case_insensitive_unique")

    def setUp(self):
        super().setUp()
        self.migrator = Migrator(database="default")
        old_state = self.migrator.apply_initial_migration(self.migrate_from)
        self.dns_view_model = old_state.apps.get_model("nautobot_dns_models", "DNSView")
        self.dns_zone_model = old_state.apps.get_model("nautobot_dns_models", "DNSZone")
        self.view = self.dns_view_model.objects.create(name="Test View")
        self.other_view = self.dns_view_model.objects.create(name="Other View")

    def tearDown(self):
        # Colliding zones left behind by a failed test would make reset() abort migration 0013 again.
        self.dns_zone_model.objects.all().delete()
        self.migrator.reset()
        super().tearDown()

    def test_adds_case_insensitive_constraint(self):
        self.dns_zone_model.objects.create(name="Example.com", dns_view=self.view)
        self.dns_zone_model.objects.create(name="example.com", dns_view=self.other_view)

        new_state = self.migrator.apply_tested_migration(self.migrate_to)

        dns_zone_model = new_state.apps.get_model("nautobot_dns_models", "DNSZone")
        self.assertEqual(dns_zone_model.objects.get(dns_view__name="Test View").name, "Example.com")
        with self.assertRaises(IntegrityError), transaction.atomic():
            dns_zone_model.objects.create(name="EXAMPLE.COM", dns_view_id=self.view.pk)

    # MySQL's default case-insensitive collation rejects case variants under the unique_together that 0013 replaces.
    @skipUnless(connection.vendor == "postgresql", "Requires a case-sensitive collation to create case variants.")
    def test_aborts_on_collisions(self):
        lower = self.dns_zone_model.objects.create(name="example.com", dns_view=self.view)
        upper = self.dns_zone_model.objects.create(name="EXAMPLE.com", dns_view=self.view)

        with self.assertRaises(migration_0013.DNSZoneNameCollisionError) as context:
            self.migrator.apply_tested_migration(self.migrate_to)

        message = str(context.exception)
        self.assertTrue(message.startswith("Migration aborted:"))
        self.assertIn('View "Test View": ', message)
        self.assertIn(f'"EXAMPLE.com" (ID {upper.pk})', message)
        self.assertIn(f'"example.com" (ID {lower.pk})', message)
        self.assertEqual(self.dns_zone_model.objects.filter(dns_view=self.view).count(), 2)
