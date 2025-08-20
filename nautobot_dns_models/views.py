"""Views for nautobot_dns_models."""

from nautobot.apps.views import NautobotUIViewSet

from nautobot_dns_models import filters, forms, models, tables
from nautobot_dns_models.api import serializers


class DNSZoneUIViewSet(NautobotUIViewSet):
    """ViewSet for DNSZone views."""

    bulk_update_form_class = forms.DNSZoneBulkEditForm
    filterset_class = filters.DNSZoneFilterSet
    filterset_form_class = forms.DNSZoneFilterForm
    form_class = forms.DNSZoneForm
    lookup_field = "pk"
    queryset = models.DNSZone.objects.all()
    serializer_class = serializers.DNSZoneSerializer
    table_class = tables.DNSZoneTable
