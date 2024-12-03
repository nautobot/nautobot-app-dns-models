"""API views for dns_models."""

from nautobot.apps.api import NautobotModelViewSet

from nautobot_dns_models import filters, models
from nautobot_dns_models.api import serializers


class DnsZoneModelViewSet(NautobotModelViewSet):  # pylint: disable=too-many-ancestors
    """DnsZoneModel viewset."""

    queryset = models.DnsZoneModel.objects.all()
    serializer_class = serializers.DnsZoneModelSerializer
    filterset_class = filters.DnsZoneModelFilterSet

    # Option for modifying the default HTTP methods:
    # http_method_names = ["get", "post", "put", "patch", "delete", "head", "options", "trace"]
