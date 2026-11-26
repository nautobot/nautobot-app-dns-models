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


class NameServerRelationshipChoices(ChoiceSet):
    """How a delegation's name server relates to the zone cut (RFC 9499 §7)."""

    IN_DOMAIN = "in-domain"
    SIBLING_DOMAIN = "sibling-domain"
    UNRELATED = "unrelated"

    CHOICES = (
        (IN_DOMAIN, "In-domain"),
        (SIBLING_DOMAIN, "Sibling domain"),
        (UNRELATED, "Unrelated"),
    )
