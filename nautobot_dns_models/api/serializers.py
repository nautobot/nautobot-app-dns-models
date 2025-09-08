"""API serializers for nautobot_dns_models."""

from drf_spectacular.utils import extend_schema_field
from nautobot.apps.api import NautobotModelSerializer
from rest_framework import serializers

from nautobot_dns_models import models


class DNSZoneSerializer(NautobotModelSerializer):  # pylint: disable=too-many-ancestors
    """DNSZone Serializer."""

    url = serializers.HyperlinkedIdentityField(view_name="plugins-api:nautobot_dns_models-api:dnszone-detail")

    class Meta:
        """Meta attributes."""

        model = models.DNSZone
        fields = "__all__"

        # Option for disabling write for certain fields:
        # read_only_fields = []


class DNSRecordSerializer(NautobotModelSerializer):  # pylint: disable=too-many-ancestors
    """DNSRecord Serializer."""

    ttl = serializers.SerializerMethodField(read_only=True)

    class Meta:
        """Meta attributes."""

        model = models.DNSRecord
        fields = "__all__"

    @extend_schema_field(serializers.IntegerField)
    def get_ttl(self, instance):
        """Expose TTL property."""
        return instance.ttl


class NSRecordSerializer(DNSRecordSerializer):  # pylint: disable=too-many-ancestors
    """NSRecord Serializer."""

    url = serializers.HyperlinkedIdentityField(view_name="plugins-api:nautobot_dns_models-api:nsrecord-detail")

    class Meta:
        """Meta attributes."""

        model = models.NSRecord
        fields = "__all__"

        # Option for disabling write for certain fields:
        # read_only_fields = []


class ARecordSerializer(DNSRecordSerializer):  # pylint: disable=too-many-ancestors
    """ARecord Serializer."""

    url = serializers.HyperlinkedIdentityField(view_name="plugins-api:nautobot_dns_models-api:arecord-detail")

    class Meta:
        """Meta attributes."""

        model = models.ARecord
        fields = "__all__"

        # Option for disabling write for certain fields:
        # read_only_fields = []


class AAAARecordSerializer(DNSRecordSerializer):  # pylint: disable=too-many-ancestors
    """AAAARecord Serializer."""

    url = serializers.HyperlinkedIdentityField(view_name="plugins-api:nautobot_dns_models-api:aaaarecord-detail")

    class Meta:
        """Meta attributes."""

        model = models.AAAARecord
        fields = "__all__"

        # Option for disabling write for certain fields:
        # read_only_fields = []


class CNAMERecordSerializer(DNSRecordSerializer):  # pylint: disable=too-many-ancestors
    """CNAMERecord Serializer."""

    url = serializers.HyperlinkedIdentityField(view_name="plugins-api:nautobot_dns_models-api:cnamerecord-detail")

    class Meta:
        """Meta attributes."""

        model = models.CNAMERecord
        fields = "__all__"

        # Option for disabling write for certain fields:
        # read_only_fields = []


class MXRecordSerializer(DNSRecordSerializer):  # pylint: disable=too-many-ancestors
    """MXRecord Serializer."""

    url = serializers.HyperlinkedIdentityField(view_name="plugins-api:nautobot_dns_models-api:mxrecord-detail")

    class Meta:
        """Meta attributes."""

        model = models.MXRecord
        fields = "__all__"

        # Option for disabling write for certain fields:
        # read_only_fields = []


class TXTRecordSerializer(DNSRecordSerializer):  # pylint: disable=too-many-ancestors
    """TXTRecord Serializer."""

    url = serializers.HyperlinkedIdentityField(view_name="plugins-api:nautobot_dns_models-api:txtrecord-detail")

    class Meta:
        """Meta attributes."""

        model = models.TXTRecord
        fields = "__all__"

        # Option for disabling write for certain fields:
        # read_only_fields = []


class PTRRecordSerializer(DNSRecordSerializer):  # pylint: disable=too-many-ancestors
    """PTRRecord Serializer."""

    url = serializers.HyperlinkedIdentityField(view_name="plugins-api:nautobot_dns_models-api:ptrrecord-detail")

    class Meta:
        """Meta attributes."""

        model = models.PTRRecord
        fields = "__all__"

        # Option for disabling write for certain fields:
        # read_only_fields = []


class SRVRecordSerializer(DNSRecordSerializer):  # pylint: disable=too-many-ancestors
    """SRVRecord Serializer."""

    url = serializers.HyperlinkedIdentityField(view_name="plugins-api:nautobot_dns_models-api:srvrecord-detail")

    class Meta:
        """Meta attributes."""

        model = models.SRVRecord
        fields = "__all__"

        # Option for disabling write for certain fields:
        # read_only_fields = []
