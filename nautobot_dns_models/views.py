"""DNS Plugin Views."""

from functools import partial
from urllib.parse import urlencode

from django.contrib import messages
from django.core.exceptions import ValidationError
from django.db.models import Exists
from django.http import Http404
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils.html import format_html
from nautobot.apps import views
from nautobot.apps.forms import ConfirmationForm
from nautobot.apps.ui import (
    ButtonColorChoices,
    ObjectDetailContent,
    ObjectFieldsPanel,
    ObjectsTablePanel,
    SectionChoices,
    StatsPanel,
)
from nautobot.apps.views import get_obj_from_context
from nautobot.core.ui import object_detail

# Not re-exported through `nautobot.apps`, but this is the helper core's own bulk edit view and job
# use to resolve a selection: pk_list, "select all" with its filters, saved views, and permissions.
from nautobot.core.views.utils import get_bulk_queryset_from_view
from nautobot.ipam.tables import PrefixTable
from rest_framework.decorators import action

from nautobot_dns_models.api.serializers import (
    AAAARecordSerializer,
    ARecordSerializer,
    CNAMERecordSerializer,
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
from nautobot_dns_models.choices import DNSZoneTypeChoices
from nautobot_dns_models.filters import (
    AAAARecordFilterSet,
    ARecordFilterSet,
    CNAMERecordFilterSet,
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
    CatalogMembershipForm,
    CNAMERecordBulkEditForm,
    CNAMERecordFilterForm,
    CNAMERecordForm,
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
    DNSRegistrar,
    DNSRegistration,
    DNSView,
    DNSZone,
    MXRecord,
    NSRecord,
    PTRRecord,
    SRVRecord,
    TXTRecord,
)
from nautobot_dns_models.tables import (
    AAAARecordTable,
    ARecordTable,
    CatalogMemberZoneTable,
    CNAMERecordTable,
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


class ZoneFieldsPanel(ObjectFieldsPanel):
    """The zone's own fields, minus a catalog zone's Catalog Zone field, which cannot apply to it."""

    def get_data(self, context):
        """Drop the Catalog Zone field on a catalog zone."""
        data = super().get_data(context)
        zone = get_obj_from_context(context)
        if zone is not None and zone.is_catalog_zone:
            data.pop("catalog_zone", None)

        return data


class ZoneRecordsTablePanel(ObjectsTablePanel):
    """A table of one record type on the zone detail page, shown according to the zone's type."""

    def __init__(self, **kwargs):
        """Instantiate a zone-records panel.

        Keyword Args:
            system_managed (bool): Show this panel on catalog zones only, without write controls.
                Defaults to False, which shows it on zones whose type lets users manage records.
            **kwargs: Passed to `ObjectsTablePanel`.
        """
        self.system_managed = kwargs.pop("system_managed", False)
        table_class = kwargs.get("table_class") or self.table_class
        kwargs.setdefault("table_title", table_class.Meta.model._meta.verbose_name_plural)
        kwargs.setdefault("table_filter", "zone")
        kwargs.setdefault("max_display_count", 5)

        if self.system_managed:
            kwargs.setdefault("add_button_route", None)
            kwargs.setdefault("exclude_columns", ["zone", "actions", "comment"])
        else:
            kwargs.setdefault("exclude_columns", ["zone"])

        super().__init__(**kwargs)

    def should_render(self, context):
        """Render a user-managed panel where users manage records, or a system panel on a catalog."""
        if not super().should_render(context):
            return False

        zone = get_obj_from_context(context)
        if zone is None:
            return False

        if self.system_managed:
            return zone.is_catalog_zone

        return not zone.is_catalog_zone


class CatalogMemberZonesPanel(ObjectsTablePanel):
    """The member zones of a catalog zone, omitted on other zones."""

    def get_extra_context(self, context):
        """Label the Add button for adding a member rather than creating a zone."""
        return {**super().get_extra_context(context), "body_content_table_verbose_name": "Member Zone"}

    def should_render(self, context):
        """Render only for catalog zones."""
        if not super().should_render(context):
            return False

        zone = get_obj_from_context(context)
        return zone is not None and zone.is_catalog_zone

    def _get_table_add_url(self, context):
        """Point Add at the catalog's add-member action, which adds an existing zone rather than creating one."""
        catalog_zone = get_obj_from_context(context)
        # Offer Add only when the user may change this catalog and some zone the field would list.
        changeable = DNSZone.objects.restrict(context["request"].user, "change")
        candidates = changeable.filter(dns_view_id=catalog_zone.dns_view_id, catalog_zone__isnull=True).exclude(
            type=DNSZoneTypeChoices.TYPE_CATALOG
        )
        if not changeable.filter(Exists(candidates), pk=catalog_zone.pk).exists():
            return None

        return_url = context.get("return_url", catalog_zone.get_absolute_url())
        add_member_url = reverse("plugins:nautobot_dns_models:dnszone_add_member", kwargs={"pk": catalog_zone.pk})
        return f"{add_member_url}?{urlencode({'return_url': return_url})}"


class ZoneRegistrationPanel(ObjectsTablePanel):
    """The zone's registrar row, omitted on catalog zones, which are not registered names."""

    def should_render(self, context):
        """Render only for zones that are not catalogs."""
        if not super().should_render(context):
            return False

        zone = get_obj_from_context(context)
        return zone is not None and not zone.is_catalog_zone


class RecordStatsPanel(StatsPanel):
    """Record counts for a zone that holds user-managed records."""

    def should_render(self, context):
        """Render only where the zone permits users to manage records."""
        zone = get_obj_from_context(context)
        return zone is not None and not zone.is_catalog_zone


class AddRecordButton(object_detail.Button):
    """An Add Records menu entry, offered only on zones whose type lets users manage records."""

    def __init__(self, *, record_model, **kwargs):
        """Bind the record type this entry creates."""
        self.record_model = record_model
        kwargs.setdefault("label", record_model._meta.verbose_name)
        super().__init__(**kwargs)

    def should_render(self, context):
        """Render only where the zone's type lets users manage records."""
        if not super().should_render(context):
            return False

        zone = get_obj_from_context(context)
        return zone is not None and not zone.is_catalog_zone


class AddRecordsDropdownButton(object_detail.DropdownButton):
    """The Add Records menu, hidden when the zone's type leaves it with nothing to offer."""

    def should_render(self, context):
        """Render only while at least one record type remains on offer."""
        if not super().should_render(context):
            return False

        # `DropdownButton` filters its children but still draws itself, even with none left.
        return any(child.should_render(context) for child in self.children)


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
    queryset = DNSZone.objects.select_related("dns_view", "catalog_zone__dns_view")
    table_class = DNSZoneTable

    object_detail_content = ObjectDetailContent(
        panels=[
            # Left pane
            ZoneFieldsPanel(
                weight=100,
                section=SectionChoices.LEFT_HALF,
                fields="__all__",
                exclude_fields=["member_label"],
            ),
            ZoneRegistrationPanel(
                weight=200,
                section=SectionChoices.LEFT_HALF,
                table_filter="dns_zone",
                table_class=DNSRegistrationTable,
                table_title="Registration",
                include_columns=["dns_registrar", "status", "expiration_date", "auto_renewal", "actions"],
                max_display_count=1,
            ),
            # Same weight: only one of these renders, so they occupy the same left-pane slot.
            ZoneRecordsTablePanel(
                weight=300,
                section=SectionChoices.LEFT_HALF,
                table_class=NSRecordTable,
            ),
            ZoneRecordsTablePanel(
                weight=300,
                section=SectionChoices.LEFT_HALF,
                table_class=NSRecordTable,
                system_managed=True,
            ),
            ZoneRecordsTablePanel(
                weight=400,
                section=SectionChoices.LEFT_HALF,
                table_class=TXTRecordTable,
                system_managed=True,
            ),
            CatalogMemberZonesPanel(
                weight=100,
                section=SectionChoices.RIGHT_HALF,
                table_class=CatalogMemberZoneTable,
                table_filter="catalog_zone",
                table_title="Member Zones",
                order_by_fields=["name"],
                max_display_count=5,
                footer_content_template_path="nautobot_dns_models/panels/member_zones_footer.html",
            ),
            # Right pane
            RecordStatsPanel(
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
            ZoneRecordsTablePanel(
                weight=100,
                section=SectionChoices.RIGHT_HALF,
                table_class=ARecordTable,
            ),
            ZoneRecordsTablePanel(
                weight=200,
                section=SectionChoices.RIGHT_HALF,
                table_class=AAAARecordTable,
            ),
            ZoneRecordsTablePanel(
                weight=300,
                section=SectionChoices.RIGHT_HALF,
                table_class=CNAMERecordTable,
            ),
            ZoneRecordsTablePanel(
                weight=400,
                section=SectionChoices.RIGHT_HALF,
                table_class=MXRecordTable,
            ),
            ZoneRecordsTablePanel(
                weight=500,
                section=SectionChoices.RIGHT_HALF,
                table_class=PTRRecordTable,
            ),
            ZoneRecordsTablePanel(
                weight=600,
                section=SectionChoices.RIGHT_HALF,
                table_class=SRVRecordTable,
            ),
            ZoneRecordsTablePanel(
                weight=700,
                section=SectionChoices.RIGHT_HALF,
                table_class=TXTRecordTable,
            ),
        ],
        extra_buttons=[
            AddRecordsDropdownButton(
                weight=100,
                color=ButtonColorChoices.BLUE,
                label="Add Records",
                icon="mdi-plus-thick",
                required_permissions=["nautobot_dns_models.change_dnszone"],
                children=(
                    AddRecordButton(
                        weight=100,
                        record_model=ARecord,
                        link_name="plugins:nautobot_dns_models:zone_a_records_add",
                        required_permissions=["nautobot_dns_models.add_arecord"],
                    ),
                    AddRecordButton(
                        weight=200,
                        record_model=AAAARecord,
                        link_name="plugins:nautobot_dns_models:zone_aaaa_records_add",
                        required_permissions=["nautobot_dns_models.add_aaaarecord"],
                    ),
                    AddRecordButton(
                        weight=300,
                        record_model=CNAMERecord,
                        link_name="plugins:nautobot_dns_models:zone_cname_records_add",
                        required_permissions=["nautobot_dns_models.add_cnamerecord"],
                    ),
                    AddRecordButton(
                        weight=400,
                        record_model=MXRecord,
                        link_name="plugins:nautobot_dns_models:zone_mx_records_add",
                        required_permissions=["nautobot_dns_models.add_mxrecord"],
                    ),
                    AddRecordButton(
                        weight=500,
                        record_model=NSRecord,
                        link_name="plugins:nautobot_dns_models:zone_ns_records_add",
                        required_permissions=["nautobot_dns_models.add_nsrecord"],
                    ),
                    AddRecordButton(
                        weight=600,
                        record_model=PTRRecord,
                        link_name="plugins:nautobot_dns_models:zone_ptr_records_add",
                        required_permissions=["nautobot_dns_models.add_ptrrecord"],
                    ),
                    AddRecordButton(
                        weight=700,
                        record_model=SRVRecord,
                        link_name="plugins:nautobot_dns_models:zone_srv_records_add",
                        required_permissions=["nautobot_dns_models.add_srvrecord"],
                    ),
                    AddRecordButton(
                        weight=800,
                        record_model=TXTRecord,
                        link_name="plugins:nautobot_dns_models:zone_txt_records_add",
                        required_permissions=["nautobot_dns_models.add_txtrecord"],
                    ),
                ),
            ),
        ],
    )

    @action(
        detail=True,
        methods=["get", "post"],
        url_path="add-member",
        url_name="add_member",
        custom_view_base_action="change",
    )
    def add_member(self, request, *args, **kwargs):
        """Add an existing zone to this catalog zone."""
        catalog_zone = self.get_object()
        if not catalog_zone.is_catalog_zone:
            raise Http404

        return self._catalog_membership_form_response(
            request,
            title=f"Add Member to Catalog Zone {catalog_zone}",
            add_another=True,
            catalog_zone=catalog_zone,
        )

    @action(
        detail=True,
        methods=["get", "post"],
        url_path="add-to-catalog",
        url_name="add_to_catalog",
        custom_view_base_action="change",
    )
    def add_to_catalog(self, request, *args, **kwargs):
        """Add this zone to a catalog zone."""
        zone = self.get_object()
        if zone.is_catalog_zone or zone.catalog_zone_id is not None:
            raise Http404

        return self._catalog_membership_form_response(
            request,
            title=f"Add Zone {zone} to a Catalog Zone",
            add_another=False,
            zone=zone,
        )

    @action(
        detail=True,
        methods=["get", "post"],
        url_path="remove-from-catalog",
        url_name="remove_from_catalog",
        custom_view_base_action="change",
    )
    def remove_from_catalog(self, request, *args, **kwargs):
        """Remove this zone from its catalog zone, after confirmation."""
        zone = self.get_object()
        catalog_zone = zone.catalog_zone
        if catalog_zone is None:
            raise Http404

        return_url = self.get_return_url(request, catalog_zone)
        if request.method == "POST":
            form = ConfirmationForm(request.POST)
            if form.is_valid():
                zone.catalog_zone = None
                try:
                    zone.validated_save()
                    messages.success(
                        request,
                        format_html(
                            'Removed <a href="{}">{}</a> from catalog zone <a href="{}">{}</a>',
                            zone.get_absolute_url(),
                            zone,
                            catalog_zone.get_absolute_url(),
                            catalog_zone,
                        ),
                    )
                except ValidationError as error:
                    messages.error(request, " ".join(error.messages))

                return redirect(return_url)
        else:
            form = ConfirmationForm(initial=request.GET)

        return render(
            request,
            "nautobot_dns_models/dnszone_remove_from_catalog.html",
            {
                "catalog_zone": catalog_zone,
                "form": form,
                "return_url": return_url,
                "zone": zone,
            },
        )

    def get_form_class(self, **kwargs):
        """Bind the edit form to the user, and the bulk edit form to the zones it will reach."""
        if self.action == "bulk_update":
            # Core builds the form from the posted zones, which under "select all" are only those on
            # the page that submitted, while the job it queues edits everything the filter matched.
            selection = get_bulk_queryset_from_view(user=self.request.user, action="change", **self.key_params)
            return partial(super().get_form_class(**kwargs), selection=selection, user=self.request.user)

        form_class = super().get_form_class(**kwargs)
        if self.action in ("create", "update"):
            # A subclass rather than a partial, since core reads the class's `base_fields`.
            user = self.request.user

            class UserBoundForm(form_class):
                """The edit form, bound to the requesting user."""

                def __init__(self, *args, **kwargs):
                    """Pass the requesting user to the form."""
                    super().__init__(*args, user=user, **kwargs)

            return UserBoundForm

        return form_class

    def _catalog_membership_form_response(self, request, *, title, add_another, catalog_zone=None, zone=None):
        """Render or process the form pairing a zone with a catalog zone, given one of the two, and return to the given one."""
        if catalog_zone is not None:
            given_zone, form_field_name = catalog_zone, "zone"
        else:
            given_zone, form_field_name = zone, "catalog_zone"
        return_url = self.get_return_url(request, given_zone)
        if request.method == "POST":
            form = CatalogMembershipForm(request.POST, user=request.user, catalog_zone=catalog_zone, zone=zone)
            if form.is_valid():
                if catalog_zone is None:
                    catalog_zone = form.cleaned_data["catalog_zone"]
                else:
                    zone = form.cleaned_data["zone"]
                zone.catalog_zone = catalog_zone
                try:
                    zone.validated_save()
                    messages.success(
                        request,
                        format_html(
                            'Added <a href="{}">{}</a> to catalog zone <a href="{}">{}</a>',
                            zone.get_absolute_url(),
                            zone,
                            catalog_zone.get_absolute_url(),
                            catalog_zone,
                        ),
                    )
                    if add_another and "_addanother" in request.POST:
                        return redirect(request.get_full_path())

                    return redirect(return_url)
                except ValidationError as error:
                    form.add_error(form_field_name, error.messages)
        else:
            form = CatalogMembershipForm(user=request.user, catalog_zone=catalog_zone, zone=zone)

        return render(
            request,
            "nautobot_dns_models/dnszone_catalog_membership.html",
            {
                "add_another": add_another,
                "form": form,
                "return_url": return_url,
                "title": title,
            },
        )


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
