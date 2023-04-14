"""API serializers for nautobot_dns_models."""
from rest_framework import serializers

from nautobot.core.api.serializers import ValidatedModelSerializer

from nautobot_dns_models import models

from . import nested_serializers  # noqa: F401, pylint: disable=unused-import


class DnsZoneModelSerializer(ValidatedModelSerializer):
    """DnsZoneModel Serializer."""

    url = serializers.HyperlinkedIdentityField(view_name="plugins-api:nautobot_dns_models-api:dnszonemodel-detail")

    class Meta:
        """Meta attributes."""

        model = models.DnsZoneModel
        fields = "__all__"

        # Option for disabling write for certain fields:
        # read_only_fields = []
