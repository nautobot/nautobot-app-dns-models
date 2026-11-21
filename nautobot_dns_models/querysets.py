"""QuerySets for Nautobot DNS Models."""

from django.apps import apps
from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import ProtectedError
from nautobot.apps.models import RestrictedQuerySet

from nautobot_dns_models.choices import DNSZoneTypeChoices
from nautobot_dns_models.system_writes import system_write, system_write_in_progress

SYSTEM_MANAGED_DELETE_ERROR = "System-managed records cannot be deleted directly."

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
        """Refuse the membership fields, and renaming members, which this would write without publishing the member PTR."""
        # `update()` would refuse these too, but only inside Django's atomic block, leaving the caller's
        # transaction unusable.
        self._refuse_membership_fields(fields)
        objs = list(objs)
        if "name" in fields:
            # Stored membership, since an instance in hand may predate a change to its catalog.
            stored_zones = self.filter(pk__in=[obj.pk for obj in objs])
            stored_zones._refuse_member_renames()  # pylint: disable=protected-access

        return super().bulk_update(objs, fields, *args, **kwargs)

    def delete(self):
        """Withdraw member PTR records and clear system-managed records, then delete the zones."""
        with transaction.atomic():
            # Nothing protects the records in the purge, but if the delete fails (e.g. due to
            # PROTECT from a member zone), the records are restored.
            self.prepare_for_delete()
            return super().delete()

    def update(self, **kwargs):
        """Refuse the membership fields, and renaming members, which this would write without publishing the member PTR."""
        self._refuse_membership_fields(kwargs)
        if "name" in kwargs:
            self._refuse_member_renames()

        return super().update(**kwargs)

    def prepare_for_delete(self):
        """Withdraw the member PTR records of these zones and clear their system-managed records.

        Run it in the same transaction as the delete, so that a refused delete keeps the records.
        """
        self._withdraw_member_ptr_records()
        self._purge_system_managed_records()

    @staticmethod
    def _refuse_membership_fields(fields):
        """Raise if `fields` names a catalog membership field."""
        if refused := sorted(set(fields) & CATALOG_MEMBERSHIP_FIELDS):
            raise ValidationError(
                f"These fields cannot be written through a queryset; save each zone instead: {', '.join(refused)}."
            )

    def _refuse_member_renames(self):
        """Raise if this holds a catalog member, whose PTR record names it and which a rename gives a new label."""
        if self.filter(catalog_zone__isnull=False).exists():
            raise ValidationError("Catalog member zones cannot be renamed through a queryset; save each zone instead.")

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

    def delete(self):
        """Refuse to delete system-managed records, as `DNSRecord.delete()` does for one record."""
        # Nautobot's bulk delete job calls `QuerySet.delete()` directly, bypassing `DNSRecord.delete()`.
        if not system_write_in_progress():
            protected = self.filter(zone__type=DNSZoneTypeChoices.TYPE_CATALOG)
            if protected.exists():
                raise ProtectedError(SYSTEM_MANAGED_DELETE_ERROR, list(protected[:50]))

        return super().delete()


def dns_record_models():
    """Return every concrete DNSRecord subclass registered with Django."""
    return [
        model
        for model in apps.get_models()
        if isinstance(model._default_manager.all(), DNSRecordQuerySet)  # pylint: disable=protected-access
    ]
