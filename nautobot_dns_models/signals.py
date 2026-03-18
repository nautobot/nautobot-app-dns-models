"""Signal handlers for automatic SOA serial number incrementing."""

from .models import (
    AAAARecord,
    ARecord,
    CNAMERecord,
    MXRecord,
    NSRecord,
    PTRRecord,
    SRVRecord,
    TXTRecord,
)

# All concrete record types that should trigger a zone serial increment.
RECORD_MODELS = (ARecord, AAAARecord, PTRRecord, CNAMERecord, NSRecord, MXRecord, SRVRecord, TXTRecord)


def _increment_zone_serial(sender, instance, **kwargs):  # pylint: disable=unused-argument
    """Increment the parent zone's SOA serial after a record is saved or deleted."""
    if hasattr(instance, "zone_id") and instance.zone_id:
        instance.zone.increment_soa_serial()


def connect_signals():
    """Connect post_save and post_delete signals for all DNS record types."""
    from django.db.models.signals import post_delete, post_save  # pylint: disable=import-outside-toplevel

    for model in RECORD_MODELS:
        post_save.connect(_increment_zone_serial, sender=model, dispatch_uid=f"soa_serial_post_save_{model.__name__}")
        post_delete.connect(
            _increment_zone_serial, sender=model, dispatch_uid=f"soa_serial_post_delete_{model.__name__}"
        )
