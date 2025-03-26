"""DNS Plugin Views."""

from nautobot.apps import views
from nautobot.apps.ui import (
    ButtonColorChoices,
    ObjectDetailContent,
    ObjectFieldsPanel,
    ObjectsTablePanel,
    SectionChoices,
    StatsPanel,
)
from nautobot.core.ui import object_detail

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
    TXTRecordModelTable,
)


class DNSZoneModelUIViewSet(views.NautobotUIViewSet):
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
            # Left pane
            ObjectFieldsPanel(
                weight=100,
                section=SectionChoices.LEFT_HALF,
                fields="__all__",
            ),
            ObjectsTablePanel(
                weight=200,
                section=SectionChoices.LEFT_HALF,
                table_filter="zone",
                table_class=NSRecordModelTable,
                table_title="NS Records",
                exclude_columns=["zone"],
                max_display_count=5,
            ),
            # Right pane
            StatsPanel(
                weight=10,
                section=SectionChoices.RIGHT_HALF,
                label="Records Statistics",
                filter_name="zone",
                related_models=[
                    ARecordModel,
                    AAAARecordModel,
                    CNAMERecordModel,
                    MXRecordModel,
                    PTRRecordModel,
                    TXTRecordModel,
                ],
            ),
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
                table_class=PTRRecordModelTable,
                table_title="PTR Records",
                exclude_columns=["zone"],
                max_display_count=5,
            ),
            ObjectsTablePanel(
                weight=600,
                section=SectionChoices.RIGHT_HALF,
                table_filter="zone",
                table_class=TXTRecordModelTable,
                table_title="TXT Records",
                exclude_columns=["zone"],
                max_display_count=5,
            ),
        ],
        extra_buttons=[
            object_detail.DropdownButton(
                weight=100,
                color=ButtonColorChoices.BLUE,
                label="Add Records",
                icon="mdi-plus-thick",
                required_permissions=["nautobot_dns_models.change_dnszonemodel"],
                children=(
                    object_detail.Button(
                        weight=100,
                        link_name="plugins:nautobot_dns_models:zone_a_records_add",
                        label="A Record",
                        required_permissions=["nautobot_dns_models.add_arecordmodel"],
                    ),
                    object_detail.Button(
                        weight=200,
                        link_name="plugins:nautobot_dns_models:zone_aaaa_records_add",
                        label="AAAA Record",
                        required_permissions=["nautobot_dns_models.add_aaaarecordmodel"],
                    ),
                    object_detail.Button(
                        weight=300,
                        link_name="plugins:nautobot_dns_models:zone_cname_records_add",
                        label="CNAME Record",
                        required_permissions=["nautobot_dns_models.add_cnamerecordmodel"],
                    ),
                    object_detail.Button(
                        weight=400,
                        link_name="plugins:nautobot_dns_models:zone_mx_records_add",
                        label="MX Record",
                        required_permissions=["nautobot_dns_models.add_mxrecordmodel"],
                    ),
                    object_detail.Button(
                        weight=500,
                        link_name="plugins:nautobot_dns_models:zone_ns_records_add",
                        label="NS Record",
                        required_permissions=["nautobot_dns_models.add_nsrecordmodel"],
                    ),
                    object_detail.Button(
                        weight=600,
                        link_name="plugins:nautobot_dns_models:zone_ptr_records_add",
                        label="PTR Record",
                        required_permissions=["nautobot_dns_models.add_ptrrecordmodel"],
                    ),
                    object_detail.Button(
                        weight=700,
                        link_name="plugins:nautobot_dns_models:zone_txt_records_add",
                        label="TXT Record",
                        required_permissions=["nautobot_dns_models.add_txtrecordmodel"],
                    ),
                ),
            ),
        ],
    )


class NSRecordModelUIViewSet(views.NautobotUIViewSet):
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


class ARecordModelUIViewSet(views.NautobotUIViewSet):
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


class AAAARecordModelUIViewSet(views.NautobotUIViewSet):
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


class CNAMERecordModelUIViewSet(views.NautobotUIViewSet):
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


class MXRecordModelUIViewSet(views.NautobotUIViewSet):
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


class TXTRecordModelUIViewSet(views.NautobotUIViewSet):
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


class PTRRecordModelUIViewSet(views.NautobotUIViewSet):
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
