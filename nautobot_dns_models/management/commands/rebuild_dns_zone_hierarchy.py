"""Recompute the parent of every DNS zone."""

from django.core.management.base import BaseCommand

from nautobot_dns_models.models import rebuild_zone_hierarchy


class Command(BaseCommand):
    """Recompute the parent of every DNS zone.

    Zone parents are kept current on save. Run this after changing zones in ways that bypass save,
    such as `QuerySet.update()`, `bulk_create()` or direct SQL.
    """

    help = "Recompute the parent of every DNS zone."

    def handle(self, *args, **options):
        """Entry point to the management command."""
        changed = rebuild_zone_hierarchy()
        self.stdout.write(self.style.SUCCESS(f"Updated the parent of {changed} DNS zone(s)."))
