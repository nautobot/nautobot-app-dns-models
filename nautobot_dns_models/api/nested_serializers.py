"""API nested serializers for nautobot_dns_models."""
from rest_framework import serializers

from nautobot.core.api import WritableNestedSerializer

from nautobot_dns_models import models


class DnsZoneModelNestedSerializer(WritableNestedSerializer):
    """DnsZoneModel Nested Serializer."""

    url = serializers.HyperlinkedIdentityField(view_name="plugins-api:nautobot_dns_models-api:dnszonemodel-detail")

    class Meta:
        """Meta attributes."""

        model = models.DnsZoneModel
        fields = "__all__"
