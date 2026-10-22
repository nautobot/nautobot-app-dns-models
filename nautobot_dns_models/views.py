"""DNS Plugin Views."""

from django.core.exceptions import ValidationError
from django.utils.html import format_html, format_html_join
from nautobot.apps import views
from nautobot.apps.forms import restrict_form_fields
from nautobot.apps.ui import (
    ButtonColorChoices,
    DataTablePanel,
    KeyValueTablePanel,
    ObjectDetailContent,
    ObjectFieldsPanel,
    ObjectsTablePanel,
    SectionChoices,
    StatsPanel,
)
from nautobot.core.templatetags.helpers import hyperlinked_object
from nautobot.core.ui import object_detail
from nautobot.core.views.utils import get_obj_from_context
from nautobot.ipam.tables import PrefixTable

from nautobot_dns_models.api.serializers import (
    AAAARecordSerializer,
    ARecordSerializer,
    CNAMERecordSerializer,
    DNSForwardingRuleSerializer,
    DNSRegistrarSerializer,
    DNSRegistrationSerializer,
    DNSViewSerializer,
    DNSZoneSerializer,
    MXRecordSerializer,
    NSRecordSerializer,
    PTRRecordSerializer,
    SRVRecordSerializer,
    TXTRecordSerializer,
)
from nautobot_dns_models.filters import (
    AAAARecordFilterSet,
    ARecordFilterSet,
    CNAMERecordFilterSet,
    DNSForwardingRuleFilterSet,
    DNSRegistrarFilterSet,
    DNSRegistrationFilterSet,
    DNSViewFilterSet,
    DNSZoneFilterSet,
    MXRecordFilterSet,
    NSRecordFilterSet,
    PTRRecordFilterSet,
    SRVRecordFilterSet,
    TXTRecordFilterSet,
)
from nautobot_dns_models.forms import (
    AAAARecordBulkEditForm,
    AAAARecordFilterForm,
    AAAARecordForm,
    ARecordBulkEditForm,
    ARecordFilterForm,
    ARecordForm,
    CNAMERecordBulkEditForm,
    CNAMERecordFilterForm,
    CNAMERecordForm,
    DNSForwardingRuleBulkEditForm,
    DNSForwardingRuleFilterForm,
    DNSForwardingRuleForm,
    DNSForwardingRuleIPAddressAssignmentFormSet,
    DNSRegistrarBulkEditForm,
    DNSRegistrarFilterForm,
    DNSRegistrarForm,
    DNSRegistrationBulkEditForm,
    DNSRegistrationFilterForm,
    DNSRegistrationForm,
    DNSViewBulkEditForm,
    DNSViewFilterForm,
    DNSViewForm,
    DNSZoneBulkEditForm,
    DNSZoneFilterForm,
    DNSZoneForm,
    MXRecordBulkEditForm,
    MXRecordFilterForm,
    MXRecordForm,
    NSRecordBulkEditForm,
    NSRecordFilterForm,
    NSRecordForm,
    PTRRecordBulkEditForm,
    PTRRecordFilterForm,
    PTRRecordForm,
    SRVRecordBulkEditForm,
    SRVRecordFilterForm,
    SRVRecordForm,
    TXTRecordBulkEditForm,
    TXTRecordFilterForm,
    TXTRecordForm,
)
from nautobot_dns_models.models import (
    AAAARecord,
    ARecord,
    CNAMERecord,
    DNSForwardingRule,
    DNSRegistrar,
    DNSRegistration,
    DNSView,
    DNSZone,
    MXRecord,
    NSRecord,
    PTRRecord,
    SRVRecord,
    TXTRecord,
    is_same_or_subdomain,
    normalize_dns_name,
    record_fqdn,
)
from nautobot_dns_models.tables import (
    AAAARecordTable,
    ARecordTable,
    CNAMERecordTable,
    DNSForwardingRuleIPAddressAssignmentTable,
    DNSForwardingRuleTable,
    DNSRegistrarTable,
    DNSRegistrationTable,
    DNSViewTable,
    DNSZoneTable,
    MXRecordTable,
    NSRecordTable,
    PTRRecordTable,
    SRVRecordTable,
    TXTRecordTable,
)


class NonEmptyDataTablePanel(DataTablePanel):
    """A DataTablePanel that is hidden when its context data is empty."""

    def should_render(self, context):
        """Render only when there are rows to show."""
        return super().should_render(context) and bool(context.get(self.context_data_key))


class NonEmptyObjectsTablePanel(ObjectsTablePanel):
    """An ObjectsTablePanel that is hidden when the filtered queryset is empty."""

    def should_render(self, context):
        """Render only when at least one related object exists."""
        if not super().should_render(context):
            return False
        obj = get_obj_from_context(context)
        queryset = self.table_class.Meta.model.objects.restrict(context["request"].user, "view")
        return queryset.filter(**{self.table_filter: obj}).exists()


def _lines(values):
    """Render values one per line, escaping each of them."""
    return format_html_join(format_html("<br>"), "{}", ((value,) for value in values))


def _delegation_rows(zone, delegations):
    """Return DataTablePanel rows describing the delegations of `zone`."""
    return [
        {
            "name": delegation.fqdn,
            "servers": _lines(delegation.servers),
            "glue": _lines(
                f"{record_fqdn(record.name, zone.name)} ({record.ip_address.host})"
                for record in delegation.glue_records
            ),
            "child_zone": hyperlinked_object(delegation.child_zone) if delegation.child_zone else "External",
        }
        for delegation in delegations
    ]


def _parent_delegation_data(zone, parent_delegations):
    """Return KeyValueTablePanel data describing how the parent zone delegates `zone`, or {} without a parent.

    The delegation may be for this zone's own name or for a name above it.
    """
    if zone.parent_zone is None:
        return {}
    zone_fqdn = normalize_dns_name(zone.name)
    delegation = next((d for d in parent_delegations if is_same_or_subdomain(zone_fqdn, d.fqdn)), None)
    return {
        "parent_zone": zone.parent_zone,
        "delegated": delegation is not None,
        "delegated_name": delegation.fqdn if delegation else None,
        "name_servers_in_parent": _lines(delegation.servers) if delegation else None,
    }


class DNSViewUIViewSet(views.NautobotUIViewSet):
    """DNSView UI ViewSet."""

    form_class = DNSViewForm
    bulk_update_form_class = DNSViewBulkEditForm
    filterset_class = DNSViewFilterSet
    filterset_form_class = DNSViewFilterForm
    serializer_class = DNSViewSerializer
    lookup_field = "pk"
    queryset = DNSView.objects.all()
    table_class = DNSViewTable

    object_detail_content = ObjectDetailContent(
        panels=[
            ObjectFieldsPanel(
                weight=100,
                section=SectionChoices.LEFT_HALF,
                fields="__all__",
            ),
            ObjectsTablePanel(
                weight=100,
                section=SectionChoices.RIGHT_HALF,
                table_filter="dns_view",
                table_class=DNSZoneTable,
                table_title="Zones",
                include_columns=["name", "ttl", "filename", "soa_rname", "actions"],
            ),
            ObjectsTablePanel(
                weight=200,
                section=SectionChoices.RIGHT_HALF,
                table_filter="dns_views",
                related_field_name="nautobot_dns_models_dns_views",
                table_class=PrefixTable,
                table_title="Assigned Prefixes",
                include_columns=["prefix", "status", "location_count", "namespace"],
            ),
        ],
    )


class DNSRegistrarUIViewSet(views.NautobotUIViewSet):
    """DNSRegistrar UI ViewSet."""

    form_class = DNSRegistrarForm
    bulk_update_form_class = DNSRegistrarBulkEditForm
    filterset_class = DNSRegistrarFilterSet
    filterset_form_class = DNSRegistrarFilterForm
    serializer_class = DNSRegistrarSerializer
    lookup_field = "pk"
    queryset = DNSRegistrar.objects.all()
    table_class = DNSRegistrarTable

    object_detail_content = ObjectDetailContent(
        panels=[
            ObjectFieldsPanel(
                weight=100,
                section=SectionChoices.LEFT_HALF,
                fields="__all__",
            ),
            ObjectsTablePanel(
                weight=100,
                section=SectionChoices.RIGHT_HALF,
                table_filter="dns_registrar",
                table_class=DNSRegistrationTable,
                table_title="Registrations",
                include_columns=["dns_zone", "status", "expiration_date", "auto_renewal", "actions"],
            ),
        ],
    )


class DNSRegistrationUIViewSet(views.NautobotUIViewSet):
    """DNSRegistration UI ViewSet."""

    form_class = DNSRegistrationForm
    bulk_update_form_class = DNSRegistrationBulkEditForm
    filterset_class = DNSRegistrationFilterSet
    filterset_form_class = DNSRegistrationFilterForm
    serializer_class = DNSRegistrationSerializer
    lookup_field = "pk"
    queryset = DNSRegistration.objects.all()
    table_class = DNSRegistrationTable

    object_detail_content = ObjectDetailContent(
        panels=[
            ObjectFieldsPanel(
                weight=100,
                section=SectionChoices.LEFT_HALF,
                fields="__all__",
            ),
        ],
    )


class DNSZoneUIViewSet(views.NautobotUIViewSet):
    """DNSZone UI ViewSet."""

    form_class = DNSZoneForm
    bulk_update_form_class = DNSZoneBulkEditForm
    filterset_class = DNSZoneFilterSet
    filterset_form_class = DNSZoneFilterForm
    serializer_class = DNSZoneSerializer
    lookup_field = "pk"
    # parent_zone is rendered with DNSZone.__str__, which includes the zone's view.
    queryset = DNSZone.objects.select_related("dns_view", "parent_zone__dns_view")
    table_class = DNSZoneTable

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
                table_filter="dns_zone",
                table_class=DNSRegistrationTable,
                table_title="Registration",
                include_columns=["dns_registrar", "status", "expiration_date", "auto_renewal", "actions"],
                max_display_count=1,
            ),
            NonEmptyDataTablePanel(
                weight=150,
                section=SectionChoices.LEFT_HALF,
                label="Delegation Checks",
                css_class="warning",
                context_data_key="zone_delegation_warnings",
                columns=["warning"],
            ),
            ObjectsTablePanel(
                weight=300,
                section=SectionChoices.LEFT_HALF,
                table_filter="zone",
                table_class=NSRecordTable,
                table_title="NS Records",
                exclude_columns=["zone"],
                max_display_count=5,
            ),
            KeyValueTablePanel(
                weight=350,
                section=SectionChoices.LEFT_HALF,
                label="Parent Delegation",
                context_data_key="zone_parent_delegation",
            ),
            NonEmptyDataTablePanel(
                weight=400,
                section=SectionChoices.LEFT_HALF,
                label="Delegations",
                context_data_key="zone_delegations",
                columns=["name", "servers", "glue", "child_zone"],
                column_headers=["Delegated Name", "Name Servers", "Glue", "Child Zone"],
            ),
            NonEmptyObjectsTablePanel(
                weight=500,
                section=SectionChoices.LEFT_HALF,
                table_filter="parent_zone",
                table_class=DNSZoneTable,
                table_title="Child Zones",
                exclude_columns=["parent_zone", "soa_expire", "soa_rname"],
                add_button_route=None,
            ),
            # Right pane
            StatsPanel(
                weight=10,
                section=SectionChoices.RIGHT_HALF,
                label="Records Statistics",
                filter_name="zone",
                related_models=[
                    ARecord,
                    AAAARecord,
                    CNAMERecord,
                    MXRecord,
                    PTRRecord,
                    SRVRecord,
                    TXTRecord,
                ],
            ),
            ObjectsTablePanel(
                weight=100,
                section=SectionChoices.RIGHT_HALF,
                table_filter="zone",
                table_class=ARecordTable,
                table_title="A Records",
                exclude_columns=["zone"],
                max_display_count=5,
            ),
            ObjectsTablePanel(
                weight=200,
                section=SectionChoices.RIGHT_HALF,
                table_filter="zone",
                table_class=AAAARecordTable,
                table_title="AAAA Records",
                exclude_columns=["zone"],
                max_display_count=5,
            ),
            ObjectsTablePanel(
                weight=300,
                section=SectionChoices.RIGHT_HALF,
                table_filter="zone",
                table_class=CNAMERecordTable,
                table_title="CNAME Records",
                exclude_columns=["zone"],
                max_display_count=5,
            ),
            ObjectsTablePanel(
                weight=400,
                section=SectionChoices.RIGHT_HALF,
                table_filter="zone",
                table_class=MXRecordTable,
                table_title="MX Records",
                exclude_columns=["zone"],
                max_display_count=5,
            ),
            ObjectsTablePanel(
                weight=500,
                section=SectionChoices.RIGHT_HALF,
                table_filter="zone",
                table_class=PTRRecordTable,
                table_title="PTR Records",
                exclude_columns=["zone"],
                max_display_count=5,
            ),
            ObjectsTablePanel(
                weight=600,
                section=SectionChoices.RIGHT_HALF,
                table_filter="zone",
                table_class=SRVRecordTable,
                table_title="SRV Records",
                exclude_columns=["zone"],
                max_display_count=5,
            ),
            ObjectsTablePanel(
                weight=700,
                section=SectionChoices.RIGHT_HALF,
                table_filter="zone",
                table_class=TXTRecordTable,
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
                required_permissions=["nautobot_dns_models.change_dnszone"],
                children=(
                    object_detail.Button(
                        weight=100,
                        link_name="plugins:nautobot_dns_models:zone_a_records_add",
                        label="A Record",
                        required_permissions=["nautobot_dns_models.add_arecord"],
                    ),
                    object_detail.Button(
                        weight=200,
                        link_name="plugins:nautobot_dns_models:zone_aaaa_records_add",
                        label="AAAA Record",
                        required_permissions=["nautobot_dns_models.add_aaaarecord"],
                    ),
                    object_detail.Button(
                        weight=300,
                        link_name="plugins:nautobot_dns_models:zone_cname_records_add",
                        label="CNAME Record",
                        required_permissions=["nautobot_dns_models.add_cnamerecord"],
                    ),
                    object_detail.Button(
                        weight=400,
                        link_name="plugins:nautobot_dns_models:zone_mx_records_add",
                        label="MX Record",
                        required_permissions=["nautobot_dns_models.add_mxrecord"],
                    ),
                    object_detail.Button(
                        weight=500,
                        link_name="plugins:nautobot_dns_models:zone_ns_records_add",
                        label="NS Record",
                        required_permissions=["nautobot_dns_models.add_nsrecord"],
                    ),
                    object_detail.Button(
                        weight=600,
                        link_name="plugins:nautobot_dns_models:zone_ptr_records_add",
                        label="PTR Record",
                        required_permissions=["nautobot_dns_models.add_ptrrecord"],
                    ),
                    object_detail.Button(
                        weight=700,
                        link_name="plugins:nautobot_dns_models:zone_srv_records_add",
                        label="SRV Record",
                        required_permissions=["nautobot_dns_models.add_srvrecord"],
                    ),
                    object_detail.Button(
                        weight=800,
                        link_name="plugins:nautobot_dns_models:zone_txt_records_add",
                        label="TXT Record",
                        required_permissions=["nautobot_dns_models.add_txtrecord"],
                    ),
                ),
            ),
        ],
    )

    def get_extra_context(self, request, instance=None):
        """Add the derived delegation data shown on the zone detail page."""
        context = super().get_extra_context(request, instance)
        if self.action == "retrieve":
            delegations = instance.get_delegations()
            parent_delegations = instance.parent_zone.get_delegations() if instance.parent_zone else []
            context["zone_delegations"] = _delegation_rows(instance, delegations)
            context["zone_delegation_warnings"] = [
                {"warning": warning} for warning in instance.get_delegation_warnings(delegations, parent_delegations)
            ]
            context["zone_parent_delegation"] = _parent_delegation_data(instance, parent_delegations)
        return context


class DNSForwardingRuleUIViewSet(views.NautobotUIViewSet):
    """DNSForwardingRule UI ViewSet."""

    form_class = DNSForwardingRuleForm
    bulk_update_form_class = DNSForwardingRuleBulkEditForm
    filterset_class = DNSForwardingRuleFilterSet
    filterset_form_class = DNSForwardingRuleFilterForm
    serializer_class = DNSForwardingRuleSerializer
    lookup_field = "pk"
    queryset = DNSForwardingRule.objects.all()
    table_class = DNSForwardingRuleTable

    object_detail_content = ObjectDetailContent(
        panels=[
            ObjectFieldsPanel(
                weight=100,
                section=SectionChoices.LEFT_HALF,
                fields="__all__",
            ),
            NonEmptyDataTablePanel(
                weight=150,
                section=SectionChoices.LEFT_HALF,
                label="Rule Checks",
                css_class="warning",
                context_data_key="forwarding_rule_warnings",
                columns=["warning"],
            ),
            ObjectsTablePanel(
                weight=100,
                section=SectionChoices.RIGHT_HALF,
                table_filter="forwarding_rule",
                table_class=DNSForwardingRuleIPAddressAssignmentTable,
                table_title="Forwarders",
                exclude_columns=["forwarding_rule"],
                add_button_route=None,
                enable_related_link=False,
            ),
        ],
    )

    def get_extra_context(self, request, instance=None):
        """Add the forwarders formset to create/edit pages and the rule checks to the detail page."""
        context = super().get_extra_context(request, instance)
        if self.action in ["create", "update"]:
            forwarder_assignments = DNSForwardingRuleIPAddressAssignmentFormSet(
                instance=instance,
                data=request.POST if request.method == "POST" else None,
            )
            for assignment_form in forwarder_assignments.forms:
                restrict_form_fields(assignment_form, request.user)
            context["forwarder_assignments"] = forwarder_assignments
        if self.action == "retrieve":
            context["forwarding_rule_warnings"] = [{"warning": warning} for warning in instance.get_warnings()]
        return context

    def form_save(self, form, **kwargs):
        """Save the rule, then its forwarders. An invalid forwarder rolls back the whole save."""
        obj = super().form_save(form, **kwargs)
        forwarder_assignments = self.get_extra_context(self.request, obj)["forwarder_assignments"]
        if not forwarder_assignments.is_valid():
            # The page is re-rendered from a fresh instance, so the row errors are reported in the error banner.
            row_errors = [
                f"Forwarder {row}: {error}"
                for row, assignment_form in enumerate(forwarder_assignments.forms, start=1)
                if not assignment_form.cleaned_data.get("DELETE")
                for field_errors in assignment_form.errors.values()
                for error in field_errors
            ]
            raise ValidationError(" ".join(row_errors + list(forwarder_assignments.non_form_errors())))
        forwarder_assignments.save()
        return obj


class NSRecordUIViewSet(views.NautobotUIViewSet):
    """NSRecord UI ViewSet."""

    form_class = NSRecordForm
    bulk_update_form_class = NSRecordBulkEditForm
    filterset_class = NSRecordFilterSet
    filterset_form_class = NSRecordFilterForm
    serializer_class = NSRecordSerializer
    lookup_field = "pk"
    queryset = NSRecord.objects.all()
    table_class = NSRecordTable
    object_detail_content = ObjectDetailContent(
        panels=[
            ObjectFieldsPanel(weight=100, section=SectionChoices.LEFT_HALF, fields="__all__", additional_fields=["ttl"])
        ],
    )


class ARecordUIViewSet(views.NautobotUIViewSet):
    """ARecord UI ViewSet."""

    form_class = ARecordForm
    bulk_update_form_class = ARecordBulkEditForm
    filterset_class = ARecordFilterSet
    filterset_form_class = ARecordFilterForm
    serializer_class = ARecordSerializer
    lookup_field = "pk"
    queryset = ARecord.objects.all()
    table_class = ARecordTable
    object_detail_content = ObjectDetailContent(
        panels=[
            ObjectFieldsPanel(weight=100, section=SectionChoices.LEFT_HALF, fields="__all__", additional_fields=["ttl"])
        ]
    )


class AAAARecordUIViewSet(views.NautobotUIViewSet):
    """AAAARecord UI ViewSet."""

    form_class = AAAARecordForm
    bulk_update_form_class = AAAARecordBulkEditForm
    filterset_class = AAAARecordFilterSet
    filterset_form_class = AAAARecordFilterForm
    serializer_class = AAAARecordSerializer
    lookup_field = "pk"
    queryset = AAAARecord.objects.all()
    table_class = AAAARecordTable
    object_detail_content = ObjectDetailContent(
        panels=[
            ObjectFieldsPanel(weight=100, section=SectionChoices.LEFT_HALF, fields="__all__", additional_fields=["ttl"])
        ]
    )


class CNAMERecordUIViewSet(views.NautobotUIViewSet):
    """CNAMERecord UI ViewSet."""

    form_class = CNAMERecordForm
    bulk_update_form_class = CNAMERecordBulkEditForm
    filterset_class = CNAMERecordFilterSet
    filterset_form_class = CNAMERecordFilterForm
    serializer_class = CNAMERecordSerializer
    lookup_field = "pk"
    queryset = CNAMERecord.objects.all()
    table_class = CNAMERecordTable
    object_detail_content = ObjectDetailContent(
        panels=[
            ObjectFieldsPanel(weight=100, section=SectionChoices.LEFT_HALF, fields="__all__", additional_fields=["ttl"])
        ]
    )


class MXRecordUIViewSet(views.NautobotUIViewSet):
    """MXRecord UI ViewSet."""

    form_class = MXRecordForm
    bulk_update_form_class = MXRecordBulkEditForm
    filterset_class = MXRecordFilterSet
    filterset_form_class = MXRecordFilterForm
    serializer_class = MXRecordSerializer
    lookup_field = "pk"
    queryset = MXRecord.objects.all()
    table_class = MXRecordTable
    object_detail_content = ObjectDetailContent(
        panels=[
            ObjectFieldsPanel(weight=100, section=SectionChoices.LEFT_HALF, fields="__all__", additional_fields=["ttl"])
        ]
    )


class TXTRecordUIViewSet(views.NautobotUIViewSet):
    """TXTRecord UI ViewSet."""

    form_class = TXTRecordForm
    bulk_update_form_class = TXTRecordBulkEditForm
    filterset_class = TXTRecordFilterSet
    filterset_form_class = TXTRecordFilterForm
    serializer_class = TXTRecordSerializer
    lookup_field = "pk"
    queryset = TXTRecord.objects.all()
    table_class = TXTRecordTable
    object_detail_content = ObjectDetailContent(
        panels=[
            ObjectFieldsPanel(weight=100, section=SectionChoices.LEFT_HALF, fields="__all__", additional_fields=["ttl"])
        ]
    )


class PTRRecordUIViewSet(views.NautobotUIViewSet):
    """PTRRecord UI ViewSet."""

    form_class = PTRRecordForm
    bulk_update_form_class = PTRRecordBulkEditForm
    filterset_class = PTRRecordFilterSet
    filterset_form_class = PTRRecordFilterForm
    serializer_class = PTRRecordSerializer
    lookup_field = "pk"
    queryset = PTRRecord.objects.all()
    table_class = PTRRecordTable
    object_detail_content = ObjectDetailContent(
        panels=[
            ObjectFieldsPanel(weight=100, section=SectionChoices.LEFT_HALF, fields="__all__", additional_fields=["ttl"])
        ]
    )


class SRVRecordUIViewSet(views.NautobotUIViewSet):
    """SRVRecord UI ViewSet."""

    form_class = SRVRecordForm
    bulk_update_form_class = SRVRecordBulkEditForm
    filterset_class = SRVRecordFilterSet
    filterset_form_class = SRVRecordFilterForm
    serializer_class = SRVRecordSerializer
    lookup_field = "pk"
    queryset = SRVRecord.objects.all()
    table_class = SRVRecordTable
    object_detail_content = ObjectDetailContent(
        panels=[
            ObjectFieldsPanel(weight=100, section=SectionChoices.LEFT_HALF, fields="__all__", additional_fields=["ttl"])
        ]
    )
