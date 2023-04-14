"""Filtering for nautobot_dns_models."""

from nautobot.utilities.filters import BaseFilterSet, NameSlugSearchFilterSet

from nautobot_dns_models import models


class DnsZoneModelFilterSet(BaseFilterSet, NameSlugSearchFilterSet):
    """Filter for DnsZoneModel."""

    class Meta:
        """Meta attributes for filter."""

        model = models.DnsZoneModel

        # add any fields from the model that you would like to filter your searches by using those
        fields = ["id", "name", "slug", "description"]
