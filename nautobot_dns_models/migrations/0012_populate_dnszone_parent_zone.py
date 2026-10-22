from django.db import migrations


def populate_parent_zone(apps, schema_editor):
    """Set parent_zone on existing zones to their nearest ancestor zone in the same DNS View."""
    DNSZone = apps.get_model("nautobot_dns_models", "DNSZone")

    # Match DNSZone.find_enclosing_zone(): ancestors come from the name without a trailing dot, lowercased,
    # and are compared with the stored names lowercased.
    zones_by_view_and_name = {}
    for zone in DNSZone.objects.all():
        zones_by_view_and_name[(zone.dns_view_id, zone.name.lower())] = zone

    for (dns_view_id, _), zone in zones_by_view_and_name.items():
        labels = zone.name.rstrip(".").lower().split(".")
        parent = None
        for i in range(1, len(labels)):
            parent = zones_by_view_and_name.get((dns_view_id, ".".join(labels[i:])))
            if parent is not None:
                break
        if parent is not None:
            DNSZone.objects.filter(pk=zone.pk).update(parent_zone=parent)


class Migration(migrations.Migration):
    dependencies = [
        ("nautobot_dns_models", "0011_zone_hierarchy_and_forwarding_rules"),
    ]

    operations = [
        migrations.RunPython(populate_parent_zone, reverse_code=migrations.RunPython.noop),
    ]
