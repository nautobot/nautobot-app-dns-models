"""API serializers for dns_models."""

from nautobot.apps.api import NautobotModelSerializer, TaggedModelSerializerMixin

from dns_models import models


class DnsZoneModelSerializer(NautobotModelSerializer, TaggedModelSerializerMixin):  # pylint: disable=too-many-ancestors
    """DnsZoneModel Serializer."""

    class Meta:
        """Meta attributes."""

        model = models.DnsZoneModel
        fields = "__all__"

        # Option for disabling write for certain fields:
        # read_only_fields = []
