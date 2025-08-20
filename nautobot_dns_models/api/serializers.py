"""API serializers for nautobot_dns_models."""

from nautobot.apps.api import NautobotModelSerializer, TaggedModelSerializerMixin

from nautobot_dns_models import models


class DNSZoneSerializer(NautobotModelSerializer, TaggedModelSerializerMixin):  # pylint: disable=too-many-ancestors
    """DNSZone Serializer."""

    class Meta:
        """Meta attributes."""

        model = models.DNSZone
        fields = "__all__"

        # Option for disabling write for certain fields:
        # read_only_fields = []
