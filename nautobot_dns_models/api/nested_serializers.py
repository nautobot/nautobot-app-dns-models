"""API nested serializers for nautobot_dns_models."""

from rest_framework import serializers

from nautobot.core.api import WritableNestedSerializer

from nautobot_dns_models import models


class DnsZoneModelNestedSerializer(WritableNestedSerializer):  # pylint: disable=too-many-ancestors
    """DnsZoneModel Nested Serializer."""

    url = serializers.HyperlinkedIdentityField(view_name="plugins-api:nautobot_dns_models-api:dnszonemodel_detail")

    class Meta:
        """Meta attributes."""

        model = models.DnsZoneModel
        fields = "__all__"
