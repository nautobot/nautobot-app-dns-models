"""API serializers for nautobot_dns_models."""

from nautobot.apps.api import NautobotModelSerializer
from rest_framework import serializers

from nautobot_dns_models import models


<<<<<<< HEAD
class DNSZoneSerializer(NautobotModelSerializer):  # pylint: disable=too-many-ancestors
    """DNSZone Serializer."""

    url = serializers.HyperlinkedIdentityField(view_name="plugins-api:nautobot_dns_models-api:dnszone-detail")
=======
class DNSZoneSerializer(NautobotModelSerializer, TaggedModelSerializerMixin):  # pylint: disable=too-many-ancestors
    """DNSZone Serializer."""
>>>>>>> 443aa28 (Cookie updated by NetworkToCode Cookie Drift Manager Tool)

    class Meta:
        """Meta attributes."""

        model = models.DNSZone
<<<<<<< HEAD
        fields = "__all__"

        # Option for disabling write for certain fields:
        # read_only_fields = []


class NSRecordSerializer(NautobotModelSerializer):  # pylint: disable=too-many-ancestors
    """NSRecord Serializer."""

    url = serializers.HyperlinkedIdentityField(view_name="plugins-api:nautobot_dns_models-api:nsrecord-detail")

    class Meta:
        """Meta attributes."""

        model = models.NSRecord
        fields = "__all__"

        # Option for disabling write for certain fields:
        # read_only_fields = []


class ARecordSerializer(NautobotModelSerializer):  # pylint: disable=too-many-ancestors
    """ARecord Serializer."""

    url = serializers.HyperlinkedIdentityField(view_name="plugins-api:nautobot_dns_models-api:arecord-detail")

    class Meta:
        """Meta attributes."""

        model = models.ARecord
        fields = "__all__"

        # Option for disabling write for certain fields:
        # read_only_fields = []


class AAAARecordSerializer(NautobotModelSerializer):  # pylint: disable=too-many-ancestors
    """AAAARecord Serializer."""

    url = serializers.HyperlinkedIdentityField(view_name="plugins-api:nautobot_dns_models-api:aaaarecord-detail")

    class Meta:
        """Meta attributes."""

        model = models.AAAARecord
        fields = "__all__"

        # Option for disabling write for certain fields:
        # read_only_fields = []


class CNAMERecordSerializer(NautobotModelSerializer):  # pylint: disable=too-many-ancestors
    """CNAMERecord Serializer."""

    url = serializers.HyperlinkedIdentityField(view_name="plugins-api:nautobot_dns_models-api:cnamerecord-detail")

    class Meta:
        """Meta attributes."""

        model = models.CNAMERecord
        fields = "__all__"

        # Option for disabling write for certain fields:
        # read_only_fields = []


class MXRecordSerializer(NautobotModelSerializer):  # pylint: disable=too-many-ancestors
    """MXRecord Serializer."""

    url = serializers.HyperlinkedIdentityField(view_name="plugins-api:nautobot_dns_models-api:mxrecord-detail")

    class Meta:
        """Meta attributes."""

        model = models.MXRecord
        fields = "__all__"

        # Option for disabling write for certain fields:
        # read_only_fields = []


class TXTRecordSerializer(NautobotModelSerializer):  # pylint: disable=too-many-ancestors
    """TXTRecord Serializer."""

    url = serializers.HyperlinkedIdentityField(view_name="plugins-api:nautobot_dns_models-api:txtrecord-detail")

    class Meta:
        """Meta attributes."""

        model = models.TXTRecord
        fields = "__all__"

        # Option for disabling write for certain fields:
        # read_only_fields = []


class PTRRecordSerializer(NautobotModelSerializer):  # pylint: disable=too-many-ancestors
    """PTRRecord Serializer."""

    url = serializers.HyperlinkedIdentityField(view_name="plugins-api:nautobot_dns_models-api:ptrrecord-detail")

    class Meta:
        """Meta attributes."""

        model = models.PTRRecord
        fields = "__all__"

        # Option for disabling write for certain fields:
        # read_only_fields = []


class SRVRecordSerializer(NautobotModelSerializer):  # pylint: disable=too-many-ancestors
    """SRVRecord Serializer."""

    url = serializers.HyperlinkedIdentityField(view_name="plugins-api:nautobot_dns_models-api:srvrecord-detail")

    class Meta:
        """Meta attributes."""

        model = models.SRVRecord
=======
>>>>>>> 443aa28 (Cookie updated by NetworkToCode Cookie Drift Manager Tool)
        fields = "__all__"

        # Option for disabling write for certain fields:
        # read_only_fields = []
