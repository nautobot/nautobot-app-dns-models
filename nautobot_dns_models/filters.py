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


class NSRecordModelFilterSet(BaseFilterSet, NameSlugSearchFilterSet):
    """Filter for NSRecordModel."""

    class Meta:
        """Meta attributes for filter."""

        model = models.NSRecordModel

        # add any fields from the model that you would like to filter your searches by using those
        fields = ["id", "name", "slug", "description"]


class ARecordModelFilterSet(BaseFilterSet, NameSlugSearchFilterSet):
    """Filter for ARecordModel."""

    class Meta:
        """Meta attributes for filter."""

        model = models.ARecordModel

        # add any fields from the model that you would like to filter your searches by using those
        fields = ["id", "name", "slug", "description"]

class AAAARecordModelFilterSet(BaseFilterSet, NameSlugSearchFilterSet):
    """Filter for AAAARecordModel."""

    class Meta:
        """Meta attributes for filter."""

        model = models.AAAARecordModel

        # add any fields from the model that you would like to filter your searches by using those
        fields = ["id", "name", "slug", "description"]

class CNAMERecordModelFilterSet(BaseFilterSet, NameSlugSearchFilterSet):
    """Filter for CNAMERecordModel."""

    class Meta:
        """Meta attributes for filter."""

        model = models.CNAMERecordModel

        # add any fields from the model that you would like to filter your searches by using those
        fields = ["id", "name", "slug", "description"]

class MXRecordModelFilterSet(BaseFilterSet, NameSlugSearchFilterSet):
    """Filter for MXRecordModel."""

    class Meta:
        """Meta attributes for filter."""

        model = models.MXRecordModel

        # add any fields from the model that you would like to filter your searches by using those
        fields = ["id", "name", "slug", "description"]


class TXTRecordModelFilterSet(BaseFilterSet, NameSlugSearchFilterSet):
    """Filter for TXTRecordModel."""

    class Meta:
        """Meta attributes for filter."""

        model = models.TXTRecordModel

        # add any fields from the model that you would like to filter your searches by using those
        fields = ["id", "name", "slug", "description"]

# class SRVRecordModelFilterSet(BaseFilterSet, NameSlugSearchFilterSet):
#     """Filter for SRVRecordModel."""

#     class Meta:
#         """Meta attributes for filter."""

#         model = models.SRVRecordModel

#         # add any fields from the model that you would like to filter your searches by using those
#         fields = ["id", "name", "slug", "description"]

# class PTRRecordModelFilterSet(BaseFilterSet, NameSlugSearchFilterSet):
#     """Filter for PTRRecordModel."""

#     class Meta:
#         """Meta attributes for filter."""

#         model = models.PTRRecordModel

#         # add any fields from the model that you would like to filter your searches by using those
#         fields = ["id", "name", "slug", "description"]


# class SOARecordModelFilterSet(BaseFilterSet, NameSlugSearchFilterSet):
#     """Filter for SOARecordModel."""

#     class Meta:
#         """Meta attributes for filter."""

#         model = models.SOARecordModel

#         # add any fields from the model that you would like to filter your searches by using those
#         fields = ["id", "name", "slug", "primary_ns", "contact", "refresh", "retry", "expire", "minimum", "description"]


