"""Filtering for nautobot_dns_models."""

from nautobot.apps.filters import NameSearchFilterSet, NautobotFilterSet

from nautobot_dns_models import models


class DNSZoneFilterSet(NameSearchFilterSet, NautobotFilterSet):  # pylint: disable=too-many-ancestors
    """Filter for DNSZone."""

    class Meta:
        """Meta attributes for filter."""

        model = models.DNSZone

        # add any fields from the model that you would like to filter your searches by using those
        fields = "__all__"
