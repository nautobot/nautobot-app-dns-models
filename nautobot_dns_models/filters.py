"""Filtering for nautobot_dns_models."""

from nautobot.extras.filters import NautobotFilterSet

from nautobot_dns_models import models


class DNSZoneFilterSet(NautobotFilterSet):
    """Filter for DNSZoneModel."""

    class Meta:
        """Meta attributes for filter."""

        model = models.DNSZone
        fields = "__all__"


class NSRecordFilterSet(NautobotFilterSet):
    """Filter for NSRecord."""

    class Meta:
        """Meta attributes for filter."""

        model = models.NSRecord
        fields = "__all__"


class ARecordFilterSet(NautobotFilterSet):
    """Filter for ARecord."""

    class Meta:
        """Meta attributes for filter."""

        model = models.ARecord
        fields = "__all__"


class AAAARecordFilterSet(NautobotFilterSet):
    """Filter for AAAARecord."""

    class Meta:
        """Meta attributes for filter."""

        model = models.AAAARecord
        fields = "__all__"


class CNAMERecordFilterSet(NautobotFilterSet):
    """Filter for CNAMERecord."""

    class Meta:
        """Meta attributes for filter."""

        model = models.CNAMERecord
        fields = "__all__"


class MXRecordFilterSet(NautobotFilterSet):
    """Filter for MXRecord."""

    class Meta:
        """Meta attributes for filter."""

        model = models.MXRecord
        fields = "__all__"


class TXTRecordFilterSet(NautobotFilterSet):
    """Filter for TXTRecord."""

    class Meta:
        """Meta attributes for filter."""

        model = models.TXTRecord
        fields = "__all__"


class PTRRecordFilterSet(NautobotFilterSet):
    """Filter for PTRRecord."""

    class Meta:
        """Meta attributes for filter."""

        model = models.PTRRecord
        fields = "__all__"


class SRVRecordFilterSet(NautobotFilterSet):
    """Filter for SRVRecord."""

    class Meta:
        """Meta attributes for filter."""

        model = models.SRVRecord
        fields = "__all__"
