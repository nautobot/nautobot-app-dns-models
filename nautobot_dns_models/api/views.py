"""API views for nautobot_dns_models."""

from nautobot.apps.api import NautobotModelViewSet

from nautobot_dns_models.api.serializers import (
    AAAARecordModelSerializer,
    ARecordModelSerializer,
    CNAMERecordModelSerializer,
    DNSZoneModelSerializer,
    MXRecordModelSerializer,
    NSRecordModelSerializer,
    PTRRecordModelSerializer,
    TXTRecordModelSerializer,
)
from nautobot_dns_models.filters import (
    AAAARecordModelFilterSet,
    ARecordModelFilterSet,
    CNAMERecordModelFilterSet,
    DNSZoneModelFilterSet,
    MXRecordModelFilterSet,
    NSRecordModelFilterSet,
    PTRRecordModelFilterSet,
    TXTRecordModelFilterSet,
)
from nautobot_dns_models.models import (
    AAAARecordModel,
    ARecordModel,
    CNAMERecordModel,
    DNSZoneModel,
    MXRecordModel,
    NSRecordModel,
    PTRRecordModel,
    TXTRecordModel,
)


class DNSZoneModelViewSet(NautobotModelViewSet):  # pylint: disable=too-many-ancestors
    """DnsZoneModel API ViewSet."""

    queryset = DNSZoneModel.objects.all()
    serializer_class = DNSZoneModelSerializer
    filterset_class = DNSZoneModelFilterSet

    lookup_field = "pk"
    # Option for modifying the default HTTP methods:
    # http_method_names = ["get", "post", "put", "patch", "delete", "head", "options", "trace"]


class NSRecordModelViewSet(NautobotModelViewSet):  # pylint: disable=too-many-ancestors
    """NSRecordModel API ViewSet."""

    queryset = NSRecordModel.objects.all()
    serializer_class = NSRecordModelSerializer
    filterset_class = NSRecordModelFilterSet

    lookup_field = "pk"


class ARecordModelViewSet(NautobotModelViewSet):  # pylint: disable=too-many-ancestors
    """ARecordModel API ViewSet."""

    queryset = ARecordModel.objects.all()
    serializer_class = ARecordModelSerializer
    filterset_class = ARecordModelFilterSet

    lookup_field = "pk"


class AAAARecordModelViewSet(NautobotModelViewSet):  # pylint: disable=too-many-ancestors
    """AAAARecordModel API ViewSet."""

    queryset = AAAARecordModel.objects.all()
    serializer_class = AAAARecordModelSerializer
    filterset_class = AAAARecordModelFilterSet

    lookup_field = "pk"


class CNameRecordModelViewSet(NautobotModelViewSet):  # pylint: disable=too-many-ancestors
    """CNameRecordModel API ViewSet."""

    queryset = CNAMERecordModel.objects.all()
    serializer_class = CNAMERecordModelSerializer
    filterset_class = CNAMERecordModelFilterSet

    lookup_field = "pk"


class MXRecordModelViewSet(NautobotModelViewSet):  # pylint: disable=too-many-ancestors
    """MXRecordModel API ViewSet."""

    queryset = MXRecordModel.objects.all()
    serializer_class = MXRecordModelSerializer
    filterset_class = MXRecordModelFilterSet

    lookup_field = "pk"


class TXTRecordModelViewSet(NautobotModelViewSet):  # pylint: disable=too-many-ancestors
    """TXTRecordModel API ViewSet."""

    queryset = TXTRecordModel.objects.all()
    serializer_class = TXTRecordModelSerializer
    filterset_class = TXTRecordModelFilterSet

    lookup_field = "pk"


class PTRRecordModelViewSet(NautobotModelViewSet):  # pylint: disable=too-many-ancestors
    """PTRRecordModel API ViewSet."""

    queryset = PTRRecordModel.objects.all()
    serializer_class = PTRRecordModelSerializer
    filterset_class = PTRRecordModelFilterSet

    lookup_field = "pk"
