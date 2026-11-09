"""Report DNS zones whose names differ only by letter case within the same DNS view."""

from django.core.management.base import BaseCommand, CommandError
from django.db.models import Count

from nautobot_dns_models.models import DNSRecord, DNSZone
from nautobot_dns_models.utils import format_dns_zone_name_collisions, get_dns_zone_name_collisions

# TODO: This is useful for upgrading from 2.3.0 to next version.
# It needs to be removed in the future when nobody uses it.


class Command(BaseCommand):
    """Report DNS zones that must be resolved before DNS zone names can be unique regardless of letter case."""

    help = __doc__

    def handle(self, *args, **options):
        """Entry point to the management command."""
        collisions = get_dns_zone_name_collisions(DNSZone)
        if not collisions:
            self.stdout.write(self.style.SUCCESS("No DNS zone name collisions found."))
            return

        zone_ids = [zone.pk for group in collisions for zone in group]
        self.stdout.write(format_dns_zone_name_collisions(collisions, record_counts=self._get_record_counts(zone_ids)))
        raise CommandError("Rename, merge, or delete the colliding zones before upgrading.")

    @staticmethod
    def _get_record_counts(zone_ids):
        """Return a mapping of zone primary key to the total number of DNS records in that zone."""
        record_counts = dict.fromkeys(zone_ids, 0)
        # __subclasses__() returns direct subclasses only; every concrete record model subclasses DNSRecord directly.
        for record_model in DNSRecord.__subclasses__():
            per_zone_counts = (
                record_model.objects.filter(zone_id__in=zone_ids)
                .values("zone_id")
                .order_by()
                .annotate(count=Count("pk"))
                .values_list("zone_id", "count")
            )
            for zone_id, count in per_zone_counts:
                record_counts[zone_id] += count
        return record_counts
