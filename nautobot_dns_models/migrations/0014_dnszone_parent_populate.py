from django.db import migrations

from nautobot_dns_models.utils import compute_zone_parents


def populate_zone_parents(apps, schema_editor):
    """Set the parent of every existing zone to its most specific enclosing zone in the same DNS view."""
    DNSZone = apps.get_model("nautobot_dns_models", "DNSZone")
    parents = compute_zone_parents(DNSZone.objects.values_list("pk", "name", "dns_view_id"))

    pks_by_parent = {}
    for pk, parent_id in parents.items():
        if parent_id is not None:
            pks_by_parent.setdefault(parent_id, []).append(pk)
    for parent_id, pks in pks_by_parent.items():
        DNSZone.objects.filter(pk__in=pks).update(parent_id=parent_id)


class Migration(migrations.Migration):
    dependencies = [
        ("nautobot_dns_models", "0013_dnszone_parent"),
    ]

    operations = [
        # Reversing needs no data change: reversing 0013 drops the column.
        migrations.RunPython(populate_zone_parents, migrations.RunPython.noop),
    ]
