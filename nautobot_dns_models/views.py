"""DNS Plugin Views."""

from django.shortcuts import redirect
from nautobot.apps import views
from .models import *
from .api import serializers

from .tables import *
from .forms import *
from .filters import *


class DnsZoneModelViewSet(views.NautobotUIViewSet):
    """DnsZoneModel UI ViewSet."""

    form_class = DnsZoneModelForm
    bulk_create_form_class = DnsZoneModelBulkCreateForm
    bulk_update_form_class = DnsZoneModelBulkEditForm
    filterset_class = DnsZoneModelFilterSet
    filterset_form_class = DnsZoneModelFilterForm
    serializer_class = serializers.DnsZoneModelSerializer
    lookup_field = "pk"
    queryset = DnsZoneModel.objects.all()
    table_class = DnsZoneModelTable

    def get_extra_context(self, request, instance):
        """Return extra context data for template."""
        # instance will be true if it's not a list view
        child_records = []
        if instance is not None:
            # record, name, value, description, url
            # for record in instance.nsrecordmodel.all():
            #     child_records.append(["NS", record.name, record.nameserver, record.description])
            for record in instance.arecordmodel.all():
                child_records.append(["A", record.name, record.address, record.description, record.get_absolute_url()])
            for record in instance.aaaarecordmodel.all():
                child_records.append(
                    ["AAAA", record.name, record.address, record.description, record.get_absolute_url()]
                )
            for record in instance.cnamerecordmodel.all():
                child_records.append(
                    ["CNAME", record.name, record.alias, record.description, record.get_absolute_url()]
                )
            for record in instance.mxrecordmodel.all():
                child_records.append(
                    ["MX", record.name, record.mail_server, record.description, record.get_absolute_url()]
                )
            for record in instance.txtrecordmodel.all():
                child_records.append(["TXT", record.name, record.text, record.description, record.get_absolute_url()])

        return {"child_records": child_records}

class NSRecordModelViewSet(views.NautobotUIViewSet):
    """NSRecordModel UI ViewSet."""

    form_class = NSRecordModelForm
    bulk_update_form_class = NSRecordModelBulkEditForm
    filterset_class = NSRecordModelFilterSet
    filterset_form_class = NSRecordModelFilterForm
    serializer_class = serializers.NSRecordModelSerializer
    lookup_field = "pk"
    queryset = NSRecordModel.objects.all()
    table_class = NSRecordModelTable


class ARecordModelViewSet(views.NautobotUIViewSet):
    """ARecordModel UI ViewSet."""

    form_class = ARecordModelForm
    bulk_update_form_class = ARecordModelBulkEditForm
    filterset_class = ARecordModelFilterSet
    filterset_form_class = ARecordModelFilterForm
    serializer_class = serializers.ARecordModelSerializer
    lookup_field = "pk"
    queryset = ARecordModel.objects.all()
    table_class = ARecordModelTable


class AAAARecordModelViewSet(views.NautobotUIViewSet):
    """AAAARecordModel UI ViewSet."""

    form_class = AAAARecordModelForm
    bulk_update_form_class = AAAARecordModelBulkEditForm
    filterset_class = AAAARecordModelFilterSet
    filterset_form_class = AAAARecordModelFilterForm
    serializer_class = serializers.AAAARecordModelSerializer
    lookup_field = "pk"
    queryset = AAAARecordModel.objects.all()
    table_class = AAAARecordModelTable


class CNAMERecordModelViewSet(views.NautobotUIViewSet):
    """CNAMERecordModel UI ViewSet."""

    form_class = CNAMERecordModelForm
    bulk_update_form_class = CNAMERecordModelBulkEditForm
    filterset_class = CNAMERecordModelFilterSet
    filterset_form_class = CNAMERecordModelFilterForm
    serializer_class = serializers.CNAMERecordModelSerializer
    lookup_field = "pk"
    queryset = CNAMERecordModel.objects.all()
    table_class = CNAMERecordModelTable


class MXRecordModelViewSet(views.NautobotUIViewSet):
    """MXRecordModel UI ViewSet."""

    form_class = MXRecordModelForm
    bulk_update_form_class = MXRecordModelBulkEditForm
    filterset_class = MXRecordModelFilterSet
    filterset_form_class = MXRecordModelFilterForm
    serializer_class = serializers.MXRecordModelSerializer
    lookup_field = "pk"
    queryset = MXRecordModel.objects.all()
    table_class = MXRecordModelTable


class TXTRecordModelViewSet(views.NautobotUIViewSet):
    """TXTRecordModel UI ViewSet."""

    form_class = TXTRecordModelForm
    bulk_update_form_class = TXTRecordModelBulkEditForm
    filterset_class = TXTRecordModelFilterSet
    filterset_form_class = TXTRecordModelFilterForm
    serializer_class = serializers.TXTRecordModelSerializer
    lookup_field = "pk"
    queryset = TXTRecordModel.objects.all()
    table_class = TXTRecordModelTable

class PTRRecordModelViewSet(views.NautobotUIViewSet):
    form_class = PTRRecordModelForm
    bulk_edit_form_class = PTRRecordModelBulkEditForm
    filterset_class = PTRRecordModelFilterSet
    filterset_form_class = PTRRecordModelFilterForm
    serializer_class = serializers.PTRRecordModelSerializer
    lookup_field = "pk"
    queryset = PTRRecordModel.objects.all()
    table_class = PTRRecordModelTable

