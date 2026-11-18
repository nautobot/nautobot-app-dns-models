"""Choice sets for nautobot_dns_models."""

from nautobot.apps.choices import ChoiceSet


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
