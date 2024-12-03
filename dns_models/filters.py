"""Filtering for dns_models."""

from nautobot.apps.filters import NameSearchFilterSet, NautobotFilterSet

from dns_models import models


class DnsZoneModelFilterSet(NautobotFilterSet, NameSearchFilterSet):  # pylint: disable=too-many-ancestors
    """Filter for DnsZoneModel."""

    class Meta:
        """Meta attributes for filter."""

        model = models.DnsZoneModel

        # add any fields from the model that you would like to filter your searches by using those
        fields = ["id", "name", "description"]
