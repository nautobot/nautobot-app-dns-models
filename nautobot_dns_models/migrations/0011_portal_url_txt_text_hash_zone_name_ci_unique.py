import hashlib

import django.db.models.functions.text
from django.db import migrations, models
from django.db.models import Count
from django.db.models.functions import Lower

BACKFILL_BATCH_SIZE = 1000
COLLISION_REPORT_LIMIT = 20


class DNSZoneNameCollisionError(Exception):
    """Raised when DNS zones in the same view have names that differ only by letter case."""


def get_dns_zone_name_collisions(DNSZone):
    """Return groups of zones whose names differ only by letter case within the same DNS view."""
    zones = DNSZone.objects.annotate(name_lower=Lower("name"))
    collision_keys = (
        zones.values("dns_view", "name_lower")
        .order_by()
        .annotate(count=Count("pk"))
        .filter(count__gt=1)
        .values_list("dns_view", "name_lower")
    )
    collisions = [
        list(zones.filter(dns_view=dns_view, name_lower=name_lower).select_related("dns_view").order_by("name"))
        for dns_view, name_lower in collision_keys
    ]
    collisions.sort(key=lambda group: (group[0].dns_view.name, group[0].name.lower()))
    return collisions


def check_for_dns_zone_name_collisions(apps, schema_editor):
    """Abort the migration if any DNS zones in the same view have names that differ only by letter case."""
    DNSZone = apps.get_model("nautobot_dns_models", "DNSZone")
    collisions = get_dns_zone_name_collisions(DNSZone)
    if not collisions:
        return

    lines = [
        "Migration aborted: DNS zone names must be unique within a DNS view regardless of letter case.",
        f"Found {len(collisions)} group(s) of DNS zones whose names differ only by letter case within the same DNS view.",
    ]
    for group in collisions[:COLLISION_REPORT_LIMIT]:
        zone_descriptions = ", ".join(f'"{zone.name}" (ID {zone.pk})' for zone in group)
        lines.append(f'    View "{group[0].dns_view.name}": {zone_descriptions}')
    if len(collisions) > COLLISION_REPORT_LIMIT:
        lines.append(f"    ...and {len(collisions) - COLLISION_REPORT_LIMIT} more.")
    lines += [
        "Run `nautobot-server check_dns_zone_name_collisions` for the full report.",
        "Rename, merge, or delete the colliding zones, then run the migration again.",
    ]
    raise DNSZoneNameCollisionError("\n".join(lines))


def set_text_hash(apps, schema_editor):
    """Populate _text_hash for existing TXT records so the new uniqueness constraint can be applied.

    No collisions are possible here: the constraint being replaced already guaranteed that
    (name, text, zone) was unique, and SHA-256 does not collide in practice.
    """
    TXTRecord = apps.get_model("nautobot_dns_models", "TXTRecord")

    batch = []
    for record in TXTRecord.objects.only("id", "text").iterator(chunk_size=BACKFILL_BATCH_SIZE):
        record._text_hash = hashlib.sha256((record.text or "").encode("utf-8")).hexdigest()
        batch.append(record)
        if len(batch) >= BACKFILL_BATCH_SIZE:
            TXTRecord.objects.bulk_update(batch, ["_text_hash"])
            batch = []

    if batch:
        TXTRecord.objects.bulk_update(batch, ["_text_hash"])


class Migration(migrations.Migration):
    dependencies = [
        ("nautobot_dns_models", "0010_aaaarecord_enabled_arecord_enabled_and_more"),
    ]

    operations = [
        # Runs first so that colliding zone names abort the migration before any schema change, including on
        # MySQL, where schema changes are not transactional.
        migrations.RunPython(check_for_dns_zone_name_collisions, migrations.RunPython.noop),
        migrations.RenameField(
            model_name="dnsregistrar",
            old_name="url",
            new_name="portal_url",
        ),
        migrations.AlterField(
            model_name="dnsregistrar",
            name="portal_url",
            field=models.URLField(
                blank=True, help_text="Registrar portal URL.", max_length=500, verbose_name="Portal URL"
            ),
        ),
        # The old constraint must be dropped before `text` is altered: MySQL holds the unique index on
        # that column and cannot index a TEXT column without a prefix length (error 1170).
        migrations.AlterUniqueTogether(
            name="txtrecord",
            unique_together=set(),
        ),
        migrations.AlterField(
            model_name="txtrecord",
            name="text",
            field=models.TextField(help_text="Text for the TXT Record."),
        ),
        migrations.AddField(
            model_name="txtrecord",
            name="_text_hash",
            field=models.CharField(editable=False, max_length=64, null=True),
        ),
        migrations.RunPython(set_text_hash, reverse_code=migrations.RunPython.noop),
        migrations.AlterField(
            model_name="txtrecord",
            name="_text_hash",
            field=models.CharField(
                editable=False, help_text="SHA-256 digest of `text`, used to enforce uniqueness.", max_length=64
            ),
        ),
        migrations.AlterUniqueTogether(
            name="txtrecord",
            unique_together={("name", "zone", "_text_hash")},
        ),
        migrations.AlterUniqueTogether(
            name="dnszone",
            unique_together=set(),
        ),
        migrations.AddConstraint(
            model_name="dnszone",
            constraint=models.UniqueConstraint(
                django.db.models.functions.text.Lower("name"),
                models.F("dns_view"),
                name="nautobot_dns_models_dnszone_name_ci_unique",
                violation_error_code="dns_zone_name_not_unique",
                violation_error_message="A DNS zone with this name (ignoring letter case) already exists in this view.",
            ),
        ),
    ]
