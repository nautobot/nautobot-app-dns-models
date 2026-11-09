"""Tests that apply migrations to a database populated at an earlier migration state.

These tests are not tagged `migration_test`, because the Nautobot test runner excludes that tag by default
and CI runs only the default `invoke tests`.
"""

import importlib
from unittest import skipUnless

from django.db import IntegrityError, connection, transaction
from django.db.migrations.executor import MigrationExecutor
from nautobot.apps.testing import TransactionTestCase

migration_0011 = importlib.import_module(
    "nautobot_dns_models.migrations.0011_portal_url_txt_text_hash_zone_name_ci_unique"
)


def migrate(targets):
    """Migrate only to `targets`, without rebuilding the database, and return the models at that state."""
    executor = MigrationExecutor(connection)
    executor.migrate(targets)
    return executor.loader.project_state(targets).apps


class DNSZoneNameCaseInsensitiveUniqueMigrationTestCase(TransactionTestCase):
    """Test migration 0011, which makes DNS zone names unique within a view regardless of letter case."""

    migrate_from = ("nautobot_dns_models", "0010_aaaarecord_enabled_arecord_enabled_and_more")
    migrate_to = ("nautobot_dns_models", "0011_portal_url_txt_text_hash_zone_name_ci_unique")

    def setUp(self):
        super().setUp()
        old_apps = migrate([self.migrate_from])
        self.dns_view_model = old_apps.get_model("nautobot_dns_models", "DNSView")
        self.dns_zone_model = old_apps.get_model("nautobot_dns_models", "DNSZone")
        self.view = self.dns_view_model.objects.create(name="Test View")
        self.other_view = self.dns_view_model.objects.create(name="Other View")

    def tearDown(self):
        # Colliding zones left behind by a failed test would abort migration 0011 again.
        self.dns_zone_model.objects.all().delete()
        migrate(MigrationExecutor(connection).loader.graph.leaf_nodes())
        super().tearDown()

    def test_adds_case_insensitive_constraint(self):
        self.dns_zone_model.objects.create(name="Example.com", dns_view=self.view)
        self.dns_zone_model.objects.create(name="example.com", dns_view=self.other_view)

        new_apps = migrate([self.migrate_to])

        dns_zone_model = new_apps.get_model("nautobot_dns_models", "DNSZone")
        self.assertEqual(dns_zone_model.objects.get(dns_view__name="Test View").name, "Example.com")
        with self.assertRaises(IntegrityError), transaction.atomic():
            dns_zone_model.objects.create(name="EXAMPLE.COM", dns_view_id=self.view.pk)

    # MySQL's default case-insensitive collation rejects case variants under the unique_together that 0011 replaces.
    @skipUnless(connection.vendor == "postgresql", "Requires a case-sensitive collation to create case variants.")
    def test_aborts_on_collisions(self):
        lower = self.dns_zone_model.objects.create(name="example.com", dns_view=self.view)
        upper = self.dns_zone_model.objects.create(name="EXAMPLE.com", dns_view=self.view)

        with self.assertRaises(migration_0011.DNSZoneNameCollisionError) as context:
            migrate([self.migrate_to])

        message = str(context.exception)
        self.assertTrue(message.startswith("Migration aborted:"))
        self.assertIn('View "Test View": ', message)
        self.assertIn(f'"EXAMPLE.com" (ID {upper.pk})', message)
        self.assertIn(f'"example.com" (ID {lower.pk})', message)
        self.assertEqual(self.dns_zone_model.objects.filter(dns_view=self.view).count(), 2)
