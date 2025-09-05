"""API views for nautobot_dns_models."""

from nautobot.apps.api import NautobotModelViewSet

from nautobot_dns_models.api.serializers import (
    AAAARecordSerializer,
    ARecordSerializer,
    CNAMERecordSerializer,
    DNSZoneSerializer,
    MXRecordSerializer,
    NSRecordSerializer,
    PTRRecordSerializer,
    SRVRecordSerializer,
    TXTRecordSerializer,
)
from nautobot_dns_models.filters import (
    AAAARecordFilterSet,
    ARecordFilterSet,
    CNAMERecordFilterSet,
    DNSZoneFilterSet,
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
    DNSZone,
    MXRecord,
    NSRecord,
    PTRRecord,
    SRVRecord,
    TXTRecord,
)


class DNSZoneViewSet(NautobotModelViewSet):  # pylint: disable=too-many-ancestors
    """DNSZone API ViewSet."""

    queryset = DNSZone.objects.all()
    serializer_class = DNSZoneSerializer
    filterset_class = DNSZoneFilterSet

    lookup_field = "pk"
    # Option for modifying the default HTTP methods:
    # http_method_names = ["get", "post", "put", "patch", "delete", "head", "options", "trace"]


class NSRecordViewSet(NautobotModelViewSet):  # pylint: disable=too-many-ancestors
    """NSRecord API ViewSet."""

    queryset = NSRecord.objects.all()
    serializer_class = NSRecordSerializer
    filterset_class = NSRecordFilterSet

    lookup_field = "pk"


class ARecordViewSet(NautobotModelViewSet):  # pylint: disable=too-many-ancestors
    """ARecord API ViewSet."""

    queryset = ARecord.objects.all()
    serializer_class = ARecordSerializer
    filterset_class = ARecordFilterSet

    lookup_field = "pk"


class AAAARecordViewSet(NautobotModelViewSet):  # pylint: disable=too-many-ancestors
    """AAAARecord API ViewSet."""

    queryset = AAAARecord.objects.all()
    serializer_class = AAAARecordSerializer
    filterset_class = AAAARecordFilterSet

    lookup_field = "pk"


class CNameRecordViewSet(NautobotModelViewSet):  # pylint: disable=too-many-ancestors
    """CNameRecord API ViewSet."""

    queryset = CNAMERecord.objects.all()
    serializer_class = CNAMERecordSerializer
    filterset_class = CNAMERecordFilterSet

    lookup_field = "pk"


class MXRecordViewSet(NautobotModelViewSet):  # pylint: disable=too-many-ancestors
    """MXRecord API ViewSet."""

    queryset = MXRecord.objects.all()
    serializer_class = MXRecordSerializer
    filterset_class = MXRecordFilterSet

    lookup_field = "pk"


class TXTRecordViewSet(NautobotModelViewSet):  # pylint: disable=too-many-ancestors
    """TXTRecord API ViewSet."""

    queryset = TXTRecord.objects.all()
    serializer_class = TXTRecordSerializer
    filterset_class = TXTRecordFilterSet

    lookup_field = "pk"


class PTRRecordViewSet(NautobotModelViewSet):  # pylint: disable=too-many-ancestors
    """PTRRecord API ViewSet."""

    queryset = PTRRecord.objects.all()
    serializer_class = PTRRecordSerializer
    filterset_class = PTRRecordFilterSet

    lookup_field = "pk"


class SRVRecordViewSet(NautobotModelViewSet):  # pylint: disable=too-many-ancestors
    """SRVRecord API ViewSet."""

    queryset = SRVRecord.objects.all()
    serializer_class = SRVRecordSerializer
    filterset_class = SRVRecordFilterSet

    lookup_field = "pk"
