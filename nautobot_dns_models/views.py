"""DNS Plugin Views."""

from django_tables2 import RequestConfig
from nautobot.apps import views
from nautobot.apps.ui import (
    BaseTextPanel,
    Button,
    ButtonColorChoices,
    DropdownButton,
    ObjectDetailContent,
    ObjectFieldsPanel,
    ObjectsTablePanel,
    SectionChoices,
    StatsPanel,
)
from nautobot.core.ui import object_detail

# object_detail,
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

    object_detail_content = ObjectDetailContent(
        panels=[
            ObjectFieldsPanel(
                weight=100,
                section=SectionChoices.LEFT_HALF,
                fields="__all__",
            ),
            # StatsPanel(
            #     weight=800,
            #     section=SectionChoices.LEFT_HALF,
            #     label="Record Statistics",
            #     filter_name="zone",
            #     related_models=[ NSRecordModel],
            # ),
            ObjectsTablePanel(
                weight=100,
                section=SectionChoices.RIGHT_HALF,
                table_filter="zone",
                table_class=ARecordModelTable,
                table_title="A Records",
                exclude_columns=["zone"],
                max_display_count=5,
            ),
            ObjectsTablePanel(
                weight=200,
                section=SectionChoices.RIGHT_HALF,
                table_filter="zone",
                table_class=AAAARecordModelTable,
                table_title="AAAA Records",
                exclude_columns=["zone"],
                max_display_count=5,
            ),
            ObjectsTablePanel(
                weight=300,
                section=SectionChoices.RIGHT_HALF,
                table_filter="zone",
                table_class=CNAMERecordModelTable,
                table_title="CName Records",
                exclude_columns=["zone"],
                max_display_count=5,
            ),
            ObjectsTablePanel(
                weight=400,
                section=SectionChoices.RIGHT_HALF,
                table_filter="zone",
                table_class=MXRecordModelTable,
                table_title="MX Records",
                exclude_columns=["zone"],
                max_display_count=5,
            ),
            ObjectsTablePanel(
                weight=500,
                section=SectionChoices.RIGHT_HALF,
                table_filter="zone",
                table_class=TXTRecordModelTable,
                table_title="TXT Records",
                exclude_columns=["zone"],
                max_display_count=5,
            ),
            ObjectsTablePanel(
                weight=600,
                section=SectionChoices.RIGHT_HALF,
                table_filter="zone",
                table_class=NSRecordModelTable,
                table_title="NS Records",
                exclude_columns=["zone"],
                max_display_count=5,
            ),
            ObjectsTablePanel(
                weight=700,
                section=SectionChoices.RIGHT_HALF,
                table_filter="zone",
                table_class=PTRRecordModelTable,
                table_title="PTR Records",
                exclude_columns=["zone"],
                max_display_count=5,
            ),
        ],
        extra_buttons=[
            # Button(
            #     weight=100,
            #     label="Add A Record",
            # ),
            DropdownButton(
                weight=100,
                color=ButtonColorChoices.BLUE,
                label="Add Components",
                # icon="mdi-plus-thick",
                required_permissions=["nautobot_dns_models.change_dnszonemodel"],
                children=(
                    Button(
                        weight=100,
                        link_name="plugins:nautobot_dns_models:arecordmodel_add",
                        label="A Record",
                        icon="mdi-console",
                        required_permissions=["nautobot_dns_models.add_arecordmodel"],
                    ),
                ),
            ),
        ],
    )


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
        ],
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
