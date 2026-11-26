"""QuerySets for Nautobot DNS Models."""

from django.apps import apps
from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import ProtectedError, Q
from nautobot.apps.models import RestrictedQuerySet

from nautobot_dns_models.choices import DNSZoneTypeChoices
from nautobot_dns_models.system_writes import system_write, system_write_in_progress

SYSTEM_MANAGED_DELETE_ERROR = "System-managed records cannot be deleted directly."
SYSTEM_MANAGED_WRITE_ERROR = "Records in a catalog zone are system-managed and cannot be created or edited directly."

# The fields holding a zone's catalog membership, which only `DNSZone.save()` can keep consistent
# with the member PTR record it publishes.
CATALOG_MEMBERSHIP_FIELDS = {"catalog_zone", "catalog_zone_id", "member_label"}


class DNSZoneQuerySet(RestrictedQuerySet):
    """QuerySet for DNSZone."""

    def bulk_create(self, objs, *args, **kwargs):
        """Refuse zones in a catalog, which would be stored without a member label or a published PTR."""
        objs = list(objs)
        if any(obj.catalog_zone_id for obj in objs):
            raise ValidationError(
                "Zones cannot be added to a catalog zone through bulk_create(); save each zone instead."
            )

        return super().bulk_create(objs, *args, **kwargs)

    def bulk_update(self, objs, fields, *args, **kwargs):
        """Refuse writes that only `DNSZone.save()` can keep consistent; see `_refuse_unsafe_writes()`."""
        # `update()` would refuse these too, but only inside Django's atomic block, leaving the caller's
        # transaction unusable.
        objs = list(objs)
        fields = list(fields)

        # Stored membership, since an instance in hand may predate a change to its catalog.
        stored_zones = self.filter(pk__in=[obj.pk for obj in objs])
        stored_zones._refuse_unsafe_writes(fields)  # pylint: disable=protected-access

        return super().bulk_update(objs, fields, *args, **kwargs)

    def delete(self):
        """Withdraw member PTR records and clear system-managed records, then delete the zones."""
        with transaction.atomic():
            # Nothing protects the records in the purge, but if the delete fails (e.g. due to
            # PROTECT from a member zone), the records are restored.
            self.prepare_for_delete()
            return super().delete()

    def update(self, **kwargs):
        """Refuse writes that only `DNSZone.save()` can keep consistent; see `_refuse_unsafe_writes()`."""
        self._refuse_unsafe_writes(kwargs)

        return super().update(**kwargs)

    def prepare_for_delete(self):
        """Withdraw the member PTR records of these zones and clear their system-managed records.

        Run it in the same transaction as the delete, so that a refused delete keeps the records.
        """
        self._withdraw_member_ptr_records()
        self._purge_system_managed_records()

    def _refuse_unsafe_writes(self, fields):
        """Raise if writing `fields` to these zones would bypass what only `DNSZone.save()` keeps consistent.

        That is the catalog membership fields, `type`, the name of a catalog member, and the view of a
        catalog member or of a catalog zone with members.
        """
        fields = set(fields)
        self._refuse_membership_fields(fields)
        self._refuse_type_change(fields)
        if "name" in fields:
            self._refuse_member_renames()
        if {"dns_view", "dns_view_id"} & fields:
            self._refuse_member_moves()

    @staticmethod
    def _refuse_membership_fields(fields):
        """Raise if `fields` names a catalog membership field."""
        if refused := sorted(set(fields) & CATALOG_MEMBERSHIP_FIELDS):
            raise ValidationError(
                "These fields cannot be written through update() or bulk_update(); save each zone instead: "
                f"{', '.join(refused)}."
            )

    @staticmethod
    def _refuse_type_change(fields):
        """Raise if `fields` names `type`, which decides whether a zone's records are system-managed."""
        if "type" in fields:
            raise ValidationError({"type": "Zone type cannot be changed after creation."})

    def _refuse_member_renames(self):
        """Raise if this holds a catalog member, whose PTR record names it and which a rename gives a new label."""
        if self.filter(catalog_zone__isnull=False).exists():
            raise ValidationError(
                "Catalog member zones cannot be renamed through update() or bulk_update(); save each zone instead."
            )

    def _refuse_member_moves(self):
        """Raise if this holds a catalog member or a catalog zone with members, which must share a view."""
        if self.filter(Q(catalog_zone__isnull=False) | Q(members__isnull=False)).exists():
            raise ValidationError(
                "Catalog member zones, and catalog zones with members, cannot be moved to another view; remove "
                "the zone from its catalog, or the catalog zone's members, first."
            )

    def _withdraw_member_ptr_records(self):
        """Withdraw the PTR records of the catalog members among these zones.

        Reads the stored memberships, since an instance in hand may predate a change to its catalog.
        """
        for zone in self.filter(catalog_zone__isnull=False):
            zone.withdraw_member_ptr_record()

    def _purge_system_managed_records(self):
        """Delete the records of the catalog zones among these zones.

        Every record in a catalog zone is system-managed. `DNSRecord.zone` is PROTECT and those
        records refuse user deletes, so a catalog zone would otherwise be permanently undeletable.
        """
        managed_zone_pks = list(self.filter(type=DNSZoneTypeChoices.TYPE_CATALOG).values_list("pk", flat=True))
        if not managed_zone_pks:
            return

        with system_write():
            for record_model in dns_record_models():
                record_model.objects.filter(zone_id__in=managed_zone_pks).delete()


class DNSRecordQuerySet(RestrictedQuerySet):
    """QuerySet shared by every concrete DNSRecord subclass."""

    def bulk_create(self, objs, *args, **kwargs):
        """Refuse records in a catalog zone, as `DNSRecord.save()` does for one record."""
        objs = list(objs)
        self._refuse_catalog_zones(Q(pk__in={obj.zone_id for obj in objs}))

        return super().bulk_create(objs, *args, **kwargs)

    def bulk_update(self, objs, fields, *args, **kwargs):
        """Refuse to edit records in a catalog zone, or to move records into one."""
        # `update()` would refuse these too, but only inside Django's atomic block, leaving the caller's
        # transaction unusable.
        objs = list(objs)
        fields = list(fields)
        new_zone_ids = [obj.zone_id for obj in objs] if {"zone", "zone_id"} & set(fields) else []
        self.filter(pk__in=[obj.pk for obj in objs]).refuse_catalog_zone_writes(new_zone_ids)

        return super().bulk_update(objs, fields, *args, **kwargs)

    def delete(self):
        """Refuse to delete system-managed records, as `DNSRecord.delete()` does for one record."""
        # Nautobot's bulk delete job calls `QuerySet.delete()` directly, bypassing `DNSRecord.delete()`.
        if not system_write_in_progress():
            protected = self.filter(zone__type=DNSZoneTypeChoices.TYPE_CATALOG)
            if protected.exists():
                raise ProtectedError(SYSTEM_MANAGED_DELETE_ERROR, list(protected[:50]))

        return super().delete()

    def update(self, **kwargs):
        """Refuse to edit records in a catalog zone, or to move records into one."""
        new_zone = kwargs.get("zone", kwargs.get("zone_id"))
        # `bulk_update()` passes the new zones as an expression, after checking them itself.
        new_zone_ids = [] if hasattr(new_zone, "resolve_expression") else [getattr(new_zone, "pk", new_zone)]
        self.refuse_catalog_zone_writes(new_zone_ids)

        return super().update(**kwargs)

    def refuse_catalog_zone_writes(self, new_zone_ids=()):
        """Raise unless the app itself is writing, if any of these records, or any zone in `new_zone_ids`, is a catalog zone."""
        zones = Q(pk__in=self.values("zone_id"))
        if new_zone_ids := set(new_zone_ids) - {None}:
            zones |= Q(pk__in=new_zone_ids)
        self._refuse_catalog_zones(zones)

    def _refuse_catalog_zones(self, zones):
        """Raise unless the app itself is writing, if any zone matching `zones` is a catalog zone."""
        if system_write_in_progress():
            return

        zone_model = self.model._meta.get_field("zone").related_model
        if zone_model.objects.filter(zones, type=DNSZoneTypeChoices.TYPE_CATALOG).exists():
            raise ValidationError({"zone": SYSTEM_MANAGED_WRITE_ERROR})


def dns_record_models():
    """Return every concrete DNSRecord subclass registered with Django."""
    return [
        model
        for model in apps.get_models()
        if isinstance(model._default_manager.all(), DNSRecordQuerySet)  # pylint: disable=protected-access
    ]
