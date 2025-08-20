"""API views for nautobot_dns_models."""

from nautobot.apps.api import NautobotModelViewSet

from nautobot_dns_models import filters, models
from nautobot_dns_models.api import serializers


class DNSZoneViewSet(NautobotModelViewSet):  # pylint: disable=too-many-ancestors
    """DNSZone viewset."""

    queryset = models.DNSZone.objects.all()
    serializer_class = serializers.DNSZoneSerializer
    filterset_class = filters.DNSZoneFilterSet

    # Option for modifying the default HTTP methods:
    # http_method_names = ["get", "post", "put", "patch", "delete", "head", "options", "trace"]
