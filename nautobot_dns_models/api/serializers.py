"""API serializers for nautobot_dns_models."""

from rest_framework import serializers

from nautobot.core.api.serializers import ValidatedModelSerializer

from nautobot_dns_models import models

from . import nested_serializers  # noqa: F401, pylint: disable=unused-import


class DnsZoneModelSerializer(ValidatedModelSerializer):  # pylint: disable=too-many-ancestors
    """DnsZoneModel Serializer."""

    url = serializers.HyperlinkedIdentityField(view_name="plugins-api:nautobot_dns_models-api:dnszonemodel-detail")

    class Meta:
        """Meta attributes."""

        model = models.DnsZoneModel
        fields = "__all__"

        # Option for disabling write for certain fields:
        # read_only_fields = []


class NSRecordModelSerializer(ValidatedModelSerializer):  # pylint: disable=too-many-ancestors
    """NSRecordModel Serializer."""

    url = serializers.HyperlinkedIdentityField(view_name="plugins-api:nautobot_dns_models-api:nsrecordmodel-detail")

    class Meta:
        """Meta attributes."""

        model = models.NSRecordModel
        fields = "__all__"

        # Option for disabling write for certain fields:
        # read_only_fields = []


class ARecordModelSerializer(ValidatedModelSerializer):  # pylint: disable=too-many-ancestors
    """ARecordModel Serializer."""

    url = serializers.HyperlinkedIdentityField(view_name="plugins-api:nautobot_dns_models-api:arecordmodel-detail")

    class Meta:
        """Meta attributes."""

        model = models.ARecordModel
        fields = "__all__"

        # Option for disabling write for certain fields:
        # read_only_fields = []


class AAAARecordModelSerializer(ValidatedModelSerializer):  # pylint: disable=too-many-ancestors
    """AAAARecordModel Serializer."""

    url = serializers.HyperlinkedIdentityField(view_name="plugins-api:nautobot_dns_models-api:aaaarecordmodel-detail")

    class Meta:
        """Meta attributes."""

        model = models.AAAARecordModel
        fields = "__all__"

        # Option for disabling write for certain fields:
        # read_only_fields = []


class CNAMERecordModelSerializer(ValidatedModelSerializer):  # pylint: disable=too-many-ancestors
    """CNAMERecordModel Serializer."""

    url = serializers.HyperlinkedIdentityField(view_name="plugins-api:nautobot_dns_models-api:cnamerecordmodel-detail")

    class Meta:
        """Meta attributes."""

        model = models.CNAMERecordModel
        fields = "__all__"

        # Option for disabling write for certain fields:
        # read_only_fields = []


class MXRecordModelSerializer(ValidatedModelSerializer):  # pylint: disable=too-many-ancestors
    """MXRecordModel Serializer."""

    url = serializers.HyperlinkedIdentityField(view_name="plugins-api:nautobot_dns_models-api:mxrecordmodel-detail")

    class Meta:
        """Meta attributes."""

        model = models.MXRecordModel
        fields = "__all__"

        # Option for disabling write for certain fields:
        # read_only_fields = []


class TXTRecordModelSerializer(ValidatedModelSerializer):  # pylint: disable=too-many-ancestors
    """TXTRecordModel Serializer."""

    url = serializers.HyperlinkedIdentityField(view_name="plugins-api:nautobot_dns_models-api:txtrecordmodel-detail")

    class Meta:
        """Meta attributes."""

        model = models.TXTRecordModel
        fields = "__all__"

        # Option for disabling write for certain fields:
        # read_only_fields = []


class PTRRecordModelSerializer(ValidatedModelSerializer):  # pylint: disable=too-many-ancestors
    """PTRRecordModel Serializer."""

    url = serializers.HyperlinkedIdentityField(view_name="plugins-api:nautobot_dns_models-api:ptrrecordmodel-detail")

    class Meta:
        """Meta attributes."""

        model = models.PTRRecordModel
        fields = "__all__"

        # Option for disabling write for certain fields:
        # read_only_fields = []
