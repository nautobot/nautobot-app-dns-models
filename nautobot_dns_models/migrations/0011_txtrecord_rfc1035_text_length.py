import hashlib

from django.db import migrations, models

BACKFILL_BATCH_SIZE = 1000


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
    ]
