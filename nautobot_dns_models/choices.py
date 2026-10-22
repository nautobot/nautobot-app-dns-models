"""Choice sets for nautobot_dns_models."""

from nautobot.apps.choices import ChoiceSet


class DNSForwardingRuleActionChoices(ChoiceSet):
    """What a resolver does with queries that match a DNS forwarding rule."""

    ACTION_FORWARD_FIRST = "forward_first"
    ACTION_FORWARD_ONLY = "forward_only"
    ACTION_DO_NOT_FORWARD = "do_not_forward"

    CHOICES = (
        (ACTION_FORWARD_FIRST, "Forward first"),
        (ACTION_FORWARD_ONLY, "Forward only"),
        (ACTION_DO_NOT_FORWARD, "Do not forward"),
    )

    CSS_CLASSES = {
        ACTION_FORWARD_FIRST: "info",
        ACTION_FORWARD_ONLY: "primary",
        ACTION_DO_NOT_FORWARD: "secondary",
    }
