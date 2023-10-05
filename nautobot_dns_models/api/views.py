"""API views for nautobot_dns_models."""

from nautobot.core.api.views import ModelViewSet

from nautobot_dns_models import filters, models

from nautobot_dns_models.api import serializers


class DnsZoneModelViewSet(ModelViewSet):  # pylint: disable=too-many-ancestors
    """DnsZoneModel viewset."""

    queryset = models.DnsZoneModel.objects.all()
    serializer_class = serializers.DnsZoneModelSerializer
    filterset_class = filters.DnsZoneModelFilterSet

    lookup_field = "pk"
    # Option for modifying the default HTTP methods:
    # http_method_names = ["get", "post", "put", "patch", "delete", "head", "options", "trace"]


class ARecordModelViewSet(ModelViewSet):
    """"""

    queryset = models.ARecordModel.objects.all()
    serializer_class = serializers.ARecordModelSerializer
    filterset_class = filters.ARecordModelFilterSet

    lookup_field = "pk"


class AAAARecordModelViewSet(ModelViewSet):
    """"""

    queryset = models.AAAARecordModel.objects.all()
    serializer_class = serializers.AAAARecordModelSerializer
    filterset_class = filters.AAAARecordModelFilterSet

    lookup_field = "pk"


class CNameRecordModelViewSet(ModelViewSet):
    queryset = models.CNAMERecordModel.objects.all()
    serializer_class = serializers.CNAMERecordModelSerializer
    filterset_class = filters.CNAMERecordModelFilterSet

    lookup_field = "pk"


class MXRecordModelViewSet(ModelViewSet):
    queryset = models.MXRecordModel.objects.all()
    serializer_class = serializers.MXRecordModelSerializer
    filterset_class = filters.MXRecordModelFilterSet

    lookup_field = "pk"


class TXTRecordModelViewSet(ModelViewSet):
    queryset = models.TXTRecordModel.objects.all()
    serializer_class = serializers.TXTRecordModelSerializer
    filterset_class = filters.TXTRecordModelFilterSet

    lookup_field = "pk"
