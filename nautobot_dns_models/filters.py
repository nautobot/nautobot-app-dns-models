"""Filtering for nautobot_dns_models."""

from nautobot.extras.filters import NautobotFilterSet

from nautobot_dns_models import models


class DNSZoneModelFilterSet(NautobotFilterSet):
    """Filter for DNSZoneModel."""

    class Meta:
        """Meta attributes for filter."""

        model = models.DNSZoneModel
        fields = "__all__"


class NSRecordModelFilterSet(NautobotFilterSet):
    """Filter for NSRecordModel."""

    class Meta:
        """Meta attributes for filter."""

        model = models.NSRecordModel
        fields = "__all__"


class ARecordModelFilterSet(NautobotFilterSet):
    """Filter for ARecordModel."""

    class Meta:
        """Meta attributes for filter."""

        model = models.ARecordModel
        fields = "__all__"


class AAAARecordModelFilterSet(NautobotFilterSet):
    """Filter for AAAARecordModel."""

    class Meta:
        """Meta attributes for filter."""

        model = models.AAAARecordModel
        fields = "__all__"


class CNAMERecordModelFilterSet(NautobotFilterSet):
    """Filter for CNAMERecordModel."""

    class Meta:
        """Meta attributes for filter."""

        model = models.CNAMERecordModel
        fields = "__all__"


class MXRecordModelFilterSet(NautobotFilterSet):
    """Filter for MXRecordModel."""

    class Meta:
        """Meta attributes for filter."""

        model = models.MXRecordModel
        fields = "__all__"


class TXTRecordModelFilterSet(NautobotFilterSet):
    """Filter for TXTRecordModel."""

    class Meta:
        """Meta attributes for filter."""

        model = models.TXTRecordModel
        fields = "__all__"


class PTRRecordModelFilterSet(NautobotFilterSet):
    """Filter for PTRRecordModel."""

    class Meta:
        """Meta attributes for filter."""

        model = models.PTRRecordModel
        fields = "__all__"
