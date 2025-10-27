"""GraphQL implementation for the DNS models."""

import graphene
from nautobot.core.graphql.types import OptimizedNautobotObjectType

from nautobot_dns_models.filters import (
    AAAARecordFilterSet,
    ARecordFilterSet,
    CNAMERecordFilterSet,
    MXRecordFilterSet,
    NSRecordFilterSet,
    PTRRecordFilterSet,
    SRVRecordFilterSet,
    TXTRecordFilterSet,
)
from nautobot_dns_models.models import (
    AAAARecord,
    ARecord,
    CNAMERecord,
    DNSRecord,
    MXRecord,
    NSRecord,
    PTRRecord,
    SRVRecord,
    TXTRecord,
)


class DNSRecordType(OptimizedNautobotObjectType):
    """Graphql Type Object for the CNAMERecord model."""

    ttl = graphene.Int(description="Time to live for the DNS record, in seconds.")

    class Meta:
        """Metadata for the CNAMERecord."""

        model = DNSRecord


class NSRecordType(DNSRecordType):
    """Graphql Type Object for the NSRecord model."""

    class Meta:
        """Metadata for the NSRecord."""

        model = NSRecord
        filterset_class = NSRecordFilterSet


class ARecordType(DNSRecordType):
    """Graphql Type Object for the ARecord model."""

    class Meta:
        """Metadata for the ARecord."""

        model = ARecord
        filterset_class = ARecordFilterSet


class AAAARecordType(DNSRecordType):
    """Graphql Type Object for the AAAARecord model."""

    class Meta:
        """Metadata for the AAAARecord."""

        model = AAAARecord
        filterset_class = AAAARecordFilterSet


class CNAMERecordType(DNSRecordType):
    """Graphql Type Object for the CNAMERecord model."""

    class Meta:
        """Metadata for the CNAMERecord."""

        model = CNAMERecord
        filterset_class = CNAMERecordFilterSet


class MXRecordType(DNSRecordType):
    """Graphql Type Object for the MXRecord model."""

    class Meta:
        """Metadata for the MXRecord."""

        model = MXRecord
        filterset_class = MXRecordFilterSet


class TXTRecordType(DNSRecordType):
    """Graphql Type Object for the TXTRecord model."""

    class Meta:
        """Metadata for the TXTRecord."""

        model = TXTRecord
        filterset_class = TXTRecordFilterSet


class PTRRecordType(DNSRecordType):
    """Graphql Type Object for the PTRRecord model."""

    class Meta:
        """Metadata for the PTRRecord."""

        model = PTRRecord
        filterset_class = PTRRecordFilterSet


class SRVRecordType(DNSRecordType):
    """Graphql Type Object for the SRVRecord model."""

    class Meta:
        """Metadata for the SRVRecord."""

        model = SRVRecord
        filterset_class = SRVRecordFilterSet


graphql_types = [
    NSRecordType,
    ARecordType,
    AAAARecordType,
    CNAMERecordType,
    MXRecordType,
    TXTRecordType,
    PTRRecordType,
    SRVRecordType,
]
