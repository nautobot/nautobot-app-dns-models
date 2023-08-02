"""DNS Plugin Views."""

from nautobot.apps import views
from .models import *
from .api import serializers

from .tables import *
from .forms import *
from .filters import *

class DnsZoneModelViewSet(views.NautobotUIViewSet):
    form_class = DnsZoneModelForm
    bulk_create_form_class = DnsZoneModelBulkCreateForm
    bulk_edit_form_class = DnsZoneModelBulkEditForm
    filterset_class = DnsZoneModelFilterSet
    filterset_form_class = DnsZoneModelFilterForm
    serializer_class = serializers.DnsZoneModelSerializer
    lookup_field = "pk"
    queryset = DnsZoneModel.objects.all()
    table_class = DnsZoneModelTable


class NSRecordModelViewSet(views.NautobotUIViewSet):
    form_class = NSRecordModelForm
    bulk_edit_form_class = NSRecordModelBulkEditForm
    filterset_class = NSRecordModelFilterSet
    filterset_form_class = NSRecordModelFilterForm
    serializer_class = serializers.NSRecordModelSerializer
    lookup_field = "pk"
    queryset = NSRecordModel.objects.all()
    table_class = NSRecordModelTable


class ARecordModelViewSet(views.NautobotUIViewSet):
    form_class = ARecordModelForm
    bulk_edit_form_class = ARecordModelBulkEditForm
    filterset_class = ARecordModelFilterSet
    filterset_form_class = ARecordModelFilterForm
    serializer_class = serializers.ARecordModelSerializer
    lookup_field = "pk"
    queryset = ARecordModel.objects.all()
    table_class = ARecordModelTable


class AAAARecordModelViewSet(views.NautobotUIViewSet):
    form_class = AAAARecordModelForm
    bulk_edit_form_class = AAAARecordModelBulkEditForm
    filterset_class = AAAARecordModelFilterSet
    filterset_form_class = AAAARecordModelFilterForm
    serializer_class = serializers.AAAARecordModelSerializer
    lookup_field = "pk"
    queryset = AAAARecordModel.objects.all()
    table_class = AAAARecordModelTable


class CNAMERecordModelViewSet(views.NautobotUIViewSet):
    form_class = CNAMERecordModelForm
    bulk_edit_form_class = CNAMERecordModelBulkEditForm
    filterset_class = CNAMERecordModelFilterSet
    filterset_form_class = CNAMERecordModelFilterForm
    serializer_class = serializers.CNAMERecordModelSerializer
    lookup_field = "pk"
    queryset = CNAMERecordModel.objects.all()
    table_class = CNAMERecordModelTable


class MXRecordModelViewSet(views.NautobotUIViewSet):
    form_class = MXRecordModelForm
    bulk_edit_form_class = MXRecordModelBulkEditForm
    filterset_class = MXRecordModelFilterSet
    filterset_form_class = MXRecordModelFilterForm
    serializer_class = serializers.MXRecordModelSerializer
    lookup_field = "pk"
    queryset = MXRecordModel.objects.all()
    table_class = MXRecordModelTable


class TXTRecordModelViewSet(views.NautobotUIViewSet):
    form_class = TXTRecordModelForm
    bulk_edit_form_class = TXTRecordModelBulkEditForm
    filterset_class = TXTRecordModelFilterSet
    filterset_form_class = TXTRecordModelFilterForm
    serializer_class = serializers.TXTRecordModelSerializer
    lookup_field = "pk"
    queryset = TXTRecordModel.objects.all()
    table_class = TXTRecordModelTable

