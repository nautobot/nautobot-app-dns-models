"""Filter extensions for nautobot_dns_models."""

from nautobot.apps.filters import FilterExtension, NaturalKeyOrPKMultipleChoiceFilter
from nautobot.apps.forms import DynamicModelMultipleChoiceField

from nautobot_dns_models.models import DNSView


class PrefixFilterExtension(FilterExtension):
    """Filter extensions for ipam.Prefix."""

    model = "ipam.prefix"

    filterset_fields = {
        "nautobot_dns_models_dns_views": NaturalKeyOrPKMultipleChoiceFilter(
            queryset=DNSView.objects.all(), label="DNS Views (name or ID)", field_name="dns_views"
        )
    }

    filterform_fields = {
        "nautobot_dns_models_dns_views": DynamicModelMultipleChoiceField(
            queryset=DNSView.objects.all(),
            required=False,
            label="DNS Views",
        )
    }


filter_extensions = [PrefixFilterExtension]
