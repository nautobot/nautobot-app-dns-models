"""Filtering for nautobot_dns_models."""

from nautobot.extras.filters import NautobotFilterSet

from nautobot_dns_models import models


class DnsZoneModelFilterSet(NameSearchFilterSet, NautobotFilterSet):  # pylint: disable=too-many-ancestors
    """Filter for DnsZoneModel."""

    class Meta:
        """Meta attributes for filter."""

        model = models.DNSZoneModel
        fields = "__all__"

        # add any fields from the model that you would like to filter your searches by using those
        fields = "__all__"
