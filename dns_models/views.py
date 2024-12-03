"""Views for dns_models."""

from nautobot.apps.views import NautobotUIViewSet

from dns_models import filters, forms, models, tables
from dns_models.api import serializers


class DnsZoneModelUIViewSet(NautobotUIViewSet):
    """ViewSet for DnsZoneModel views."""

    bulk_update_form_class = forms.DnsZoneModelBulkEditForm
    filterset_class = filters.DnsZoneModelFilterSet
    filterset_form_class = forms.DnsZoneModelFilterForm
    form_class = forms.DnsZoneModelForm
    lookup_field = "pk"
    queryset = models.DnsZoneModel.objects.all()
    serializer_class = serializers.DnsZoneModelSerializer
    table_class = tables.DnsZoneModelTable
