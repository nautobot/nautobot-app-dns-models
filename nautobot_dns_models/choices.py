"""Choice sets for nautobot_dns_models."""

from nautobot.apps.choices import ChoiceSet


class NameServerBailiwickChoices(ChoiceSet):
    """Where a delegation's name server sits relative to the zone cut (RFC 9499 §7)."""

    IN_DOMAIN = "in-domain"
    SIBLING = "sibling"
    OUT_OF_BAILIWICK = "out-of-bailiwick"

    CHOICES = (
        (IN_DOMAIN, "In-domain"),
        (SIBLING, "Sibling domain"),
        (OUT_OF_BAILIWICK, "Out-of-bailiwick"),
    )
