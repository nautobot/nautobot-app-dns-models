"""Filtering for nautobot_dns_models."""

import django_filters
from django.db.models import F
from django.db.models.functions import Coalesce
from nautobot.extras.filters import NautobotFilterSet

from nautobot_dns_models import models


class DNSZoneFilterSet(NautobotFilterSet):
    """Filter for DNSZone."""

    class Meta:
        """Meta attributes for filter."""

        model = models.DNSZone
        fields = "__all__"


# pylint: disable=nb-no-model-found, nb-warn-dunder-filter-field
class DNSRecordFilterSet(NautobotFilterSet):
    """Base filter for all DNSRecord models, with support for effective TTL."""

    ttl = django_filters.NumberFilter(method="filter_ttl", label="TTL")
    ttl__ne = django_filters.NumberFilter(method="filter_ttl_ne")
    ttl__gte = django_filters.NumberFilter(method="filter_ttl", lookup_expr="gte")
    ttl__lte = django_filters.NumberFilter(method="filter_ttl", lookup_expr="lte")
    ttl__gt = django_filters.NumberFilter(method="filter_ttl", lookup_expr="gt")
    ttl__lt = django_filters.NumberFilter(method="filter_ttl", lookup_expr="lt")

    def filter_ttl(self, queryset, name, value):
        """Filter by effective TTL (use record's TTL if set, otherwise zone's TTL)."""
        queryset = queryset.annotate(effective_ttl=Coalesce(F("_ttl"), F("zone__ttl")))
        lookup = name.split("__")[-1] if "__" in name else "exact"
        return queryset.filter(**{f"effective_ttl__{lookup}": value})

    def filter_ttl_ne(self, queryset, name, value):  # pylint: disable=unused-argument
        """Exclude effective TTL equal to value."""
        queryset = queryset.annotate(effective_ttl=Coalesce(F("_ttl"), F("zone__ttl")))
        return queryset.exclude(effective_ttl=value)


class NSRecordFilterSet(DNSRecordFilterSet):
    """Filter for NSRecord."""

    class Meta:
        """Meta attributes for filter."""

        model = models.NSRecord
        fields = "__all__"


class ARecordFilterSet(DNSRecordFilterSet):
    """Filter for ARecord."""

    class Meta:
        """Meta attributes for filter."""

        model = models.ARecord
        fields = "__all__"


class AAAARecordFilterSet(DNSRecordFilterSet):
    """Filter for AAAARecord."""

    class Meta:
        """Meta attributes for filter."""

        model = models.AAAARecord
        fields = "__all__"


class CNAMERecordFilterSet(DNSRecordFilterSet):
    """Filter for CNAMERecord."""

    class Meta:
        """Meta attributes for filter."""

        model = models.CNAMERecord
        fields = "__all__"


class MXRecordFilterSet(DNSRecordFilterSet):
    """Filter for MXRecord."""

    class Meta:
        """Meta attributes for filter."""

        model = models.MXRecord
        fields = "__all__"


class TXTRecordFilterSet(DNSRecordFilterSet):
    """Filter for TXTRecord."""

    class Meta:
        """Meta attributes for filter."""

        model = models.TXTRecord
        fields = "__all__"


class PTRRecordFilterSet(DNSRecordFilterSet):
    """Filter for PTRRecord."""

    class Meta:
        """Meta attributes for filter."""

        model = models.PTRRecord
        fields = "__all__"


class SRVRecordFilterSet(DNSRecordFilterSet):
    """Filter for SRVRecord."""

    class Meta:
        """Meta attributes for filter."""

        model = models.SRVRecord
        fields = "__all__"
