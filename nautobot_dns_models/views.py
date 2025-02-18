"""DNS Plugin Views."""

from django_tables2 import RequestConfig
from nautobot.apps import views
from nautobot.apps.ui import ObjectDetailContent, ObjectFieldsPanel, SectionChoices
from nautobot.core.views.paginator import EnhancedPaginator, get_paginate_count

from nautobot_dns_models.api.serializers import (
    AAAARecordModelSerializer,
    ARecordModelSerializer,
    CNAMERecordModelSerializer,
    DNSZoneModelSerializer,
    MXRecordModelSerializer,
    NSRecordModelSerializer,
    PTRRecordModelSerializer,
    TXTRecordModelSerializer,
)
from nautobot_dns_models.filters import (
    AAAARecordModelFilterSet,
    ARecordModelFilterSet,
    CNAMERecordModelFilterSet,
    DNSZoneModelFilterSet,
    MXRecordModelFilterSet,
    NSRecordModelFilterSet,
    PTRRecordModelFilterSet,
    TXTRecordModelFilterSet,
)
from nautobot_dns_models.forms import (
    AAAARecordModelBulkEditForm,
    AAAARecordModelFilterForm,
    AAAARecordModelForm,
    ARecordModelBulkEditForm,
    ARecordModelFilterForm,
    ARecordModelForm,
    CNAMERecordModelBulkEditForm,
    CNAMERecordModelFilterForm,
    CNAMERecordModelForm,
    DNSZoneModelBulkEditForm,
    DNSZoneModelFilterForm,
    DNSZoneModelForm,
    MXRecordModelBulkEditForm,
    MXRecordModelFilterForm,
    MXRecordModelForm,
    NSRecordModelBulkEditForm,
    NSRecordModelFilterForm,
    NSRecordModelForm,
    PTRRecordModelBulkEditForm,
    PTRRecordModelFilterForm,
    PTRRecordModelForm,
    TXTRecordModelBulkEditForm,
    TXTRecordModelFilterForm,
    TXTRecordModelForm,
)
from nautobot_dns_models.models import (
    AAAARecordModel,
    ARecordModel,
    CNAMERecordModel,
    DNSZoneModel,
    MXRecordModel,
    NSRecordModel,
    PTRRecordModel,
    TXTRecordModel,
)
from nautobot_dns_models.tables import (
    AAAARecordModelTable,
    ARecordModelTable,
    CNAMERecordModelTable,
    DNSZoneModelTable,
    MXRecordModelTable,
    NSRecordModelTable,
    PTRRecordModelTable,
    RecordsTable,
    TXTRecordModelTable,
)


class DNSZoneModelViewSet(views.NautobotUIViewSet):
    """DnsZoneModel UI ViewSet."""

    form_class = DNSZoneModelForm
    bulk_update_form_class = DNSZoneModelBulkEditForm
    filterset_class = DNSZoneModelFilterSet
    filterset_form_class = DNSZoneModelFilterForm
    serializer_class = DNSZoneModelSerializer
    lookup_field = "pk"
    queryset = DNSZoneModel.objects.all()
    table_class = DNSZoneModelTable

    def get_extra_context(self, request, instance):
        """Return extra context data for template."""
        # instance will be true if it's not a list view
        child_records = []
        if instance is not None:
            for record in instance.a_records.all():
                child_records.append(record)
            for record in instance.aaaa_records.all():
                child_records.append(record)
            for record in instance.cname_records.all():
                child_records.append(record)
            for record in instance.mx_records.all():
                child_records.append(record)
            for record in instance.txt_records.all():
                child_records.append(record)
            for record in instance.ns_records.all():
                child_records.append(record)
            for record in instance.ptr_records.all():
                child_records.append(record)

        records_table = RecordsTable(
            child_records,
        )
        # add pagination for the records table.
        paginate = {
            "paginator_class": EnhancedPaginator,
            "per_page": get_paginate_count(request),
        }
        RequestConfig(request, paginate).configure(records_table)
        return {"records_table": records_table}


class NSRecordModelViewSet(views.NautobotUIViewSet):
    """NSRecordModel UI ViewSet."""

    form_class = NSRecordModelForm
    bulk_update_form_class = NSRecordModelBulkEditForm
    filterset_class = NSRecordModelFilterSet
    filterset_form_class = NSRecordModelFilterForm
    serializer_class = NSRecordModelSerializer
    lookup_field = "pk"
    queryset = NSRecordModel.objects.all()
    table_class = NSRecordModelTable
    object_detail_content = ObjectDetailContent(
        panels=[
            ObjectFieldsPanel(
                weight=100,
                section=SectionChoices.LEFT_HALF,
                fields="__all__",
            )
        ]
    )


class ARecordModelViewSet(views.NautobotUIViewSet):
    """ARecordModel UI ViewSet."""

    form_class = ARecordModelForm
    bulk_update_form_class = ARecordModelBulkEditForm
    filterset_class = ARecordModelFilterSet
    filterset_form_class = ARecordModelFilterForm
    serializer_class = ARecordModelSerializer
    lookup_field = "pk"
    queryset = ARecordModel.objects.all()
    table_class = ARecordModelTable
    object_detail_content = ObjectDetailContent(
        panels=[
            ObjectFieldsPanel(
                weight=100,
                section=SectionChoices.LEFT_HALF,
                fields="__all__",
            )
        ]
    )


class AAAARecordModelViewSet(views.NautobotUIViewSet):
    """AAAARecordModel UI ViewSet."""

    form_class = AAAARecordModelForm
    bulk_update_form_class = AAAARecordModelBulkEditForm
    filterset_class = AAAARecordModelFilterSet
    filterset_form_class = AAAARecordModelFilterForm
    serializer_class = AAAARecordModelSerializer
    lookup_field = "pk"
    queryset = AAAARecordModel.objects.all()
    table_class = AAAARecordModelTable
    object_detail_content = ObjectDetailContent(
        panels=[
            ObjectFieldsPanel(
                weight=100,
                section=SectionChoices.LEFT_HALF,
                fields="__all__",
            )
        ]
    )


class CNAMERecordModelViewSet(views.NautobotUIViewSet):
    """CNAMERecordModel UI ViewSet."""

    form_class = CNAMERecordModelForm
    bulk_update_form_class = CNAMERecordModelBulkEditForm
    filterset_class = CNAMERecordModelFilterSet
    filterset_form_class = CNAMERecordModelFilterForm
    serializer_class = CNAMERecordModelSerializer
    lookup_field = "pk"
    queryset = CNAMERecordModel.objects.all()
    table_class = CNAMERecordModelTable
    object_detail_content = ObjectDetailContent(
        panels=[
            ObjectFieldsPanel(
                weight=100,
                section=SectionChoices.LEFT_HALF,
                fields="__all__",
            )
        ]
    )


class MXRecordModelViewSet(views.NautobotUIViewSet):
    """MXRecordModel UI ViewSet."""

    form_class = MXRecordModelForm
    bulk_update_form_class = MXRecordModelBulkEditForm
    filterset_class = MXRecordModelFilterSet
    filterset_form_class = MXRecordModelFilterForm
    serializer_class = MXRecordModelSerializer
    lookup_field = "pk"
    queryset = MXRecordModel.objects.all()
    table_class = MXRecordModelTable
    object_detail_content = ObjectDetailContent(
        panels=[
            ObjectFieldsPanel(
                weight=100,
                section=SectionChoices.LEFT_HALF,
                fields="__all__",
            )
        ]
    )


class TXTRecordModelViewSet(views.NautobotUIViewSet):
    """TXTRecordModel UI ViewSet."""

    form_class = TXTRecordModelForm
    bulk_update_form_class = TXTRecordModelBulkEditForm
    filterset_class = TXTRecordModelFilterSet
    filterset_form_class = TXTRecordModelFilterForm
    serializer_class = TXTRecordModelSerializer
    lookup_field = "pk"
    queryset = TXTRecordModel.objects.all()
    table_class = TXTRecordModelTable
    object_detail_content = ObjectDetailContent(
        panels=[
            ObjectFieldsPanel(
                weight=100,
                section=SectionChoices.LEFT_HALF,
                fields="__all__",
            )
        ]
    )


class PTRRecordModelViewSet(views.NautobotUIViewSet):
    """PTRRecordModel UI ViewSet."""

    form_class = PTRRecordModelForm
    bulk_update_form_class = PTRRecordModelBulkEditForm
    filterset_class = PTRRecordModelFilterSet
    filterset_form_class = PTRRecordModelFilterForm
    serializer_class = PTRRecordModelSerializer
    lookup_field = "pk"
    queryset = PTRRecordModel.objects.all()
    table_class = PTRRecordModelTable
    object_detail_content = ObjectDetailContent(
        panels=[
            ObjectFieldsPanel(
                weight=100,
                section=SectionChoices.LEFT_HALF,
                fields="__all__",
            )
        ]
    )
