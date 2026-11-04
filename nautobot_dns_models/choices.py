"""Choices for Nautobot DNS Models."""

from nautobot.apps.choices import ChoiceSet


class DNSZoneTypeChoices(ChoiceSet):
    """Type of a DNS zone."""

    TYPE_PRIMARY = "primary"
    TYPE_CATALOG = "catalog"

    CHOICES = (
        (TYPE_PRIMARY, "Primary"),
        (TYPE_CATALOG, "Catalog"),
    )

    # The app writes the records of the other types itself.
    USER_RECORD_ZONE_TYPES = (TYPE_PRIMARY,)
