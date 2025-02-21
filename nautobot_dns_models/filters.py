"""Filtering for nautobot_dns_models."""

from nautobot.apps.filters import NaturalKeyOrPKMultipleChoiceFilter
from nautobot.extras.filters import NautobotFilterSet

from nautobot_dns_models import models


class DNSZoneModelFilterSet(NautobotFilterSet):
    """Filter for DNSZoneModel."""

    class Meta:
        """Meta attributes for filter."""

        model = models.DNSZoneModel
        fields = "__all__"


# TODO: Remove this filterset when 2.4.4 is released and the fix is incorporated
# https://github.com/nautobot/nautobot/issues/6920
# https://github.com/nautobot/nautobot/pull/6921
class RecordModelFilterSet(NautobotFilterSet):
    """Filter for every record to specify zone.

    Needed it to workaround the https://github.com/nautobot/nautobot/issues/6920.
    """

    zone = NaturalKeyOrPKMultipleChoiceFilter(
        queryset=models.DNSZoneModel.objects.all(),
        to_field_name="name",
        label="DNS Zone for the record",
    )


class NSRecordModelFilterSet(RecordModelFilterSet):
    """Filter for NSRecordModel."""

    class Meta:
        """Meta attributes for filter."""

        model = models.NSRecordModel
        fields = "__all__"


class ARecordModelFilterSet(RecordModelFilterSet):
    """Filter for ARecordModel."""

    class Meta:
        """Meta attributes for filter."""

        model = models.ARecordModel
        fields = "__all__"


class AAAARecordModelFilterSet(RecordModelFilterSet):
    """Filter for AAAARecordModel."""

    class Meta:
        """Meta attributes for filter."""

        model = models.AAAARecordModel
        fields = "__all__"


class CNAMERecordModelFilterSet(RecordModelFilterSet):
    """Filter for CNAMERecordModel."""

    class Meta:
        """Meta attributes for filter."""

        model = models.CNAMERecordModel
        fields = "__all__"


class MXRecordModelFilterSet(RecordModelFilterSet):
    """Filter for MXRecordModel."""

    class Meta:
        """Meta attributes for filter."""

        model = models.MXRecordModel
        fields = "__all__"


class TXTRecordModelFilterSet(RecordModelFilterSet):
    """Filter for TXTRecordModel."""

    class Meta:
        """Meta attributes for filter."""

        model = models.TXTRecordModel
        fields = "__all__"


class PTRRecordModelFilterSet(RecordModelFilterSet):
    """Filter for PTRRecordModel."""

    class Meta:
        """Meta attributes for filter."""

        model = models.PTRRecordModel
        fields = "__all__"
