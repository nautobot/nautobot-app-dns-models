"""Forms for nautobot_dns_models."""

# pylint: disable=too-many-lines
from django import forms
from django.db import transaction
from django.db.models import ProtectedError, RestrictedError
from django.db.models.deletion import Collector
from nautobot.apps.forms import (
    BootstrapMixin,
    BulkEditNullBooleanSelect,
    ConfirmationForm,
    DatePicker,
    DynamicModelChoiceField,
    DynamicModelMultipleChoiceField,
    NautobotBulkEditForm,
    NautobotFilterForm,
    NautobotModelForm,
    StaticSelect2,
    StaticSelect2Multiple,
    TagsBulkEditFormMixin,
)

# This should be updated after https://github.com/nautobot/nautobot/issues/9302 is resolved
from nautobot.core.forms.constants import BOOLEAN_WITH_BLANK_CHOICES
from nautobot.extras.models import Status
from nautobot.ipam.choices import IPAddressVersionChoices
from nautobot.ipam.models import IPAddress, Prefix
from nautobot.tenancy.forms import TenancyFilterForm, TenancyForm
from nautobot.tenancy.models import Tenant

from nautobot_dns_models import models
from nautobot_dns_models.choices import DNSZoneTypeChoices

EXPIRATION_DATE_INPUT_FORMATS = ("%Y-%m-%d",)


class EnabledBeforeDescriptionMixin:
    """Render the `enabled` field right before `description` on create/edit forms.

    `enabled` is declared on the abstract `DNSModel` base while the concrete models override
    `name`, so with `fields = "__all__"` Django's declaration order puts `enabled` first.
    Must be listed before the form base class so this reordering runs after the fields are built.
    """

    def __init__(self, *args, **kwargs):
        """Move `enabled` so it renders immediately before `description`."""
        super().__init__(*args, **kwargs)
        if "enabled" not in self.fields or "description" not in self.fields:
            return
        enabled = self.fields.pop("enabled")
        reordered = {}
        for field_name, field in self.fields.items():
            if field_name == "description":
                reordered["enabled"] = enabled
            reordered[field_name] = field
        self.fields = reordered


class DNSViewForm(NautobotModelForm):
    """DNSView creation/edit form."""

    prefixes = DynamicModelMultipleChoiceField(
        queryset=Prefix.objects.all(),
        required=False,
    )

    class Meta:
        """Meta attributes."""

        model = models.DNSView
        fields = "__all__"


class DNSViewBulkEditForm(TagsBulkEditFormMixin, NautobotBulkEditForm):
    """DNSView bulk edit form."""

    pk = forms.ModelMultipleChoiceField(queryset=models.DNSView.objects.all(), widget=forms.MultipleHiddenInput)
    description = forms.CharField(required=False)

    class Meta:
        """Meta attributes."""

        nullable_fields = [
            "description",
        ]


class DNSViewFilterForm(NautobotFilterForm):
    """Filter form to filter searches."""

    q = forms.CharField(
        required=False,
        label="Search",
        help_text="Search within Name and Description.",
    )
    name = forms.CharField(required=False, label="Name")
    model = models.DNSView
    # Define the fields above for ordering and widget purposes
    fields = [
        "q",
        "name",
    ]


class DNSRegistrarForm(NautobotModelForm):
    """DNSRegistrar creation/edit form."""

    class Meta:
        """Meta attributes."""

        model = models.DNSRegistrar
        fields = "__all__"


class DNSRegistrarBulkEditForm(TagsBulkEditFormMixin, NautobotBulkEditForm):
    """DNSRegistrar bulk edit form."""

    pk = forms.ModelMultipleChoiceField(queryset=models.DNSRegistrar.objects.all(), widget=forms.MultipleHiddenInput)
    portal_url = forms.URLField(required=False, label="Portal URL")
    account_number = forms.CharField(required=False)

    class Meta:
        """Meta attributes."""

        nullable_fields = [
            "portal_url",
            "account_number",
        ]


class DNSRegistrarFilterForm(NautobotFilterForm):
    """Filter form to filter searches."""

    q = forms.CharField(
        required=False,
        label="Search",
        help_text="Search within Name, Portal URL, and Account Number.",
    )
    name = forms.CharField(required=False, label="Name")
    portal_url = forms.CharField(required=False, label="Portal URL")
    account_number = forms.CharField(required=False, label="Account Number")
    model = models.DNSRegistrar
    fields = [
        "q",
        "name",
        "portal_url",
        "account_number",
    ]


class DNSRegistrationForm(NautobotModelForm):
    """DNSRegistration creation/edit form."""

    expiration_date = forms.DateField(
        required=False,
        widget=DatePicker(),
        input_formats=EXPIRATION_DATE_INPUT_FORMATS,
    )
    dns_zone = DynamicModelChoiceField(
        queryset=models.DNSZone.objects.all(),
        required=True,
        query_params={
            "type__n": DNSZoneTypeChoices.TYPE_CATALOG,
        },
        label="Zone",
    )

    class Meta:
        """Meta attributes."""

        model = models.DNSRegistration
        fields = "__all__"


class DNSRegistrationBulkEditForm(TagsBulkEditFormMixin, NautobotBulkEditForm):
    """DNSRegistration bulk edit form."""

    pk = forms.ModelMultipleChoiceField(queryset=models.DNSRegistration.objects.all(), widget=forms.MultipleHiddenInput)
    dns_registrar = DynamicModelChoiceField(
        queryset=models.DNSRegistrar.objects.all(),
        required=False,
    )
    dns_zone = DynamicModelChoiceField(
        queryset=models.DNSZone.objects.all(),
        required=False,
        query_params={
            "type__n": DNSZoneTypeChoices.TYPE_CATALOG,
        },
        label="Zone",
    )
    status = DynamicModelChoiceField(
        queryset=Status.objects.all(),
        required=False,
    )
    expiration_date = forms.DateField(
        required=False,
        widget=DatePicker(),
        input_formats=EXPIRATION_DATE_INPUT_FORMATS,
    )
    auto_renewal = forms.NullBooleanField(required=False)
    registry_locked = forms.NullBooleanField(required=False)
    transfer_locked = forms.NullBooleanField(required=False)
    privacy_enabled = forms.NullBooleanField(required=False)
    website_forwarding_enabled = forms.NullBooleanField(required=False)
    renewal_term_months = forms.IntegerField(required=False, min_value=1)
    dnssec_enabled = forms.NullBooleanField(required=False)

    class Meta:
        """Meta attributes."""

        nullable_fields = [
            "expiration_date",
            "renewal_term_months",
        ]


class DNSRegistrationFilterForm(NautobotFilterForm):
    """Filter form for DNSRegistration searches."""

    q = forms.CharField(
        required=False,
        label="Search",
        help_text="Search within Registrar and Zone.",
    )
    dns_registrar = DynamicModelChoiceField(
        queryset=models.DNSRegistrar.objects.all(),
        required=False,
        label="Registrar",
    )
    dns_zone = DynamicModelChoiceField(
        queryset=models.DNSZone.objects.all(),
        required=False,
        query_params={
            "type__n": DNSZoneTypeChoices.TYPE_CATALOG,
        },
        label="Zone",
    )
    status = DynamicModelChoiceField(
        queryset=Status.objects.all(),
        required=False,
        label="Status",
    )
    expiration_date__lte = forms.DateField(
        required=False,
        label="Expiration Date (Before)",
        widget=DatePicker(),
        input_formats=EXPIRATION_DATE_INPUT_FORMATS,
    )
    expiration_date__gte = forms.DateField(
        required=False,
        label="Expiration Date (After)",
        widget=DatePicker(),
        input_formats=EXPIRATION_DATE_INPUT_FORMATS,
    )
    auto_renewal = forms.NullBooleanField(required=False, label="Auto Renewal")
    registry_locked = forms.NullBooleanField(required=False, label="Registry Locked")
    transfer_locked = forms.NullBooleanField(required=False, label="Transfer Locked")
    privacy_enabled = forms.NullBooleanField(required=False, label="Privacy Enabled")
    website_forwarding_enabled = forms.NullBooleanField(required=False, label="Website Forwarding Enabled")
    renewal_term_months = forms.IntegerField(required=False, min_value=1, label="Renewal Term (Months)")
    dnssec_enabled = forms.NullBooleanField(required=False, label="DNSSEC Enabled")
    model = models.DNSRegistration
    fields = [
        "q",
        "dns_registrar",
        "dns_zone",
        "status",
        "expiration_date__lte",
        "expiration_date__gte",
        "auto_renewal",
        "registry_locked",
        "transfer_locked",
        "privacy_enabled",
        "website_forwarding_enabled",
        "renewal_term_months",
        "dnssec_enabled",
    ]


class DNSZoneForm(NautobotModelForm, TenancyForm):
    """DNSZone creation/edit form."""

    dns_view = DynamicModelChoiceField(
        queryset=models.DNSView.objects.all(),
        required=True,
        label="View",
    )
    catalog_zone = DynamicModelChoiceField(
        queryset=models.DNSZone.objects.filter(type=DNSZoneTypeChoices.TYPE_CATALOG),
        required=False,
        query_params={"type": DNSZoneTypeChoices.TYPE_CATALOG, "dns_view": "$dns_view"},
        label="Catalog Zone",
        help_text="The catalog zone this zone is a member of.",
    )

    field_order = ["name", "type", "dns_view", "catalog_zone", "member_label", "enabled", "auto_create_ptr"]

    class Meta:
        """Meta attributes."""

        model = models.DNSZone
        fields = "__all__"
        widgets = {"type": StaticSelect2()}

    class Media:
        """Load the toggling of the controls that depend on the zone's type and catalog zone."""

        js = ("nautobot_dns_models/js/dns_zone_form.js",)

    def __init__(self, *args, **kwargs):
        """Configure fields according to the stored zone state."""
        super().__init__(*args, **kwargs)

        # The label placeholder would read as a label on a zone in no catalog, whose field is empty.
        self.fields["member_label"].widget.attrs["placeholder"] = ""

        # The zone's label, or a generated one for a zone not yet in a catalog, offered should a
        # catalog be chosen. The script reads the data attribute, since a re-rendered form has no
        # value for a label that was disabled on submit.
        if not self.instance.is_catalog_zone:
            if not self.initial.get("member_label"):
                self.initial["member_label"] = models.catalog_member_label()
            self.fields["member_label"].widget.attrs["data-default-label"] = self.initial["member_label"]

        # New zones keep their create-time controls editable.
        if not self.instance.present_in_database:
            return

        # Every stored zone keeps its type fixed.
        self.fields["type"].disabled = True
        self.fields["type"].help_text = "Zone type cannot be changed after creation."

        # Catalog zones cannot enable automatic PTR creation, nor be members of another catalog.
        if self.instance.is_catalog_zone:
            self.fields["auto_create_ptr"].disabled = True
            self.fields["auto_create_ptr"].help_text = "Catalog zones cannot enable automatic PTR creation."
            self.fields["catalog_zone"].disabled = True
            self.fields["catalog_zone"].help_text = "A catalog zone cannot be a member of another catalog zone."
            self.fields["member_label"].disabled = True
            self.fields["member_label"].help_text = "A catalog zone has no member label."

    def clean(self):
        """Require a member label for a zone in a catalog, and drop it for any other zone."""
        super().clean()

        catalog_zone = self.cleaned_data.get("catalog_zone")
        member_label = self.cleaned_data.get("member_label")

        if not catalog_zone:
            self.cleaned_data["member_label"] = ""
        elif not member_label and not self.has_error("member_label"):
            self.add_error("member_label", "A zone in a catalog zone needs a member label.")

        return self.cleaned_data


class DNSZoneBulkEditForm(TagsBulkEditFormMixin, NautobotBulkEditForm):
    """DNSZone bulk edit form."""

    pk = forms.ModelMultipleChoiceField(queryset=models.DNSZone.objects.all(), widget=forms.MultipleHiddenInput)
    dns_view = DynamicModelChoiceField(
        queryset=models.DNSView.objects.all(),
        required=False,
        label="View",
    )
    ttl = forms.IntegerField(
        required=False,
        max_value=models.UINT32_MAX,
        label="TTL",
        help_text="Time To Live.",
    )
    soa_mname = forms.CharField(
        required=False,
        max_length=200,
        help_text="FQDN of the Authoritative Name Server for Zone.",
        label="SOA MNAME",
    )
    soa_rname = forms.CharField(
        required=False,
        max_length=254,
        help_text="Mailbox of the person responsible for the zone or a single-label placeholder.",
        label="SOA RNAME",
    )
    soa_refresh = forms.IntegerField(
        required=False,
        max_value=models.UINT32_MAX,
        help_text="Number of seconds after which secondary name servers should query the master for the SOA record, to detect zone changes.",
        label="SOA Refresh",
    )
    soa_retry = forms.IntegerField(
        required=False,
        max_value=models.UINT32_MAX,
        help_text="Number of seconds after which secondary name servers should retry to request the serial number from the master if the master does not respond.",
        label="SOA Retry",
    )
    soa_expire = forms.IntegerField(
        required=False,
        max_value=models.UINT32_MAX,
        help_text="Number of seconds after which secondary name servers should stop answering request for this zone if the master does not respond. This value must be bigger than the sum of Refresh and Retry.",
        label="SOA Expire",
    )
    soa_serial = forms.IntegerField(
        required=False,
        min_value=0,
        max_value=models.UINT32_MAX,
        help_text="Serial number of the zone. This value must be incremented each time the zone is changed, and secondary DNS servers must be able to retrieve this value to check if the zone has been updated.",
        label="SOA Serial",
    )
    soa_minimum = forms.IntegerField(
        required=False,
        max_value=models.UINT32_MAX,
        help_text="Minimum TTL for records in this zone.",
        label="SOA Minimum",
    )
    description = forms.CharField(required=False)
    tenant = DynamicModelChoiceField(
        queryset=Tenant.objects.all(),
        required=False,
    )
    auto_create_ptr = forms.NullBooleanField(
        required=False, label="Auto-create PTR Records", widget=BulkEditNullBooleanSelect
    )
    catalog_zone = DynamicModelChoiceField(
        queryset=models.DNSZone.objects.filter(type=DNSZoneTypeChoices.TYPE_CATALOG),
        required=False,
        query_params={"type": DNSZoneTypeChoices.TYPE_CATALOG},
        label="Catalog Zone",
    )
    enabled = forms.NullBooleanField(required=False, widget=BulkEditNullBooleanSelect)

    class Meta:
        """Meta attributes."""

        nullable_fields = [
            "catalog_zone",
            "description",
            "tenant",
        ]

    def __init__(self, *args, selection=None, **kwargs):
        """Take the zones this edit will reach, which the posted zones do not cover under "select all".

        The bulk edit job builds this form without `selection`, and leaves the checks it enables to
        the model.
        """
        super().__init__(*args, **kwargs)
        self.selection = selection

        catalog_zone = self.fields["catalog_zone"]
        if selection is None:
            return

        # A catalog zone refuses `auto_create_ptr` and a catalog of its own, and one refusal rolls
        # the whole batch back.
        if selection.filter(type=DNSZoneTypeChoices.TYPE_CATALOG).exists():
            auto_create_ptr = self.fields["auto_create_ptr"]
            auto_create_ptr.disabled = True
            auto_create_ptr.help_text = "Catalog zones cannot enable this, and the selection includes one."
            catalog_zone.disabled = True
            catalog_zone.help_text = "Catalog zones cannot be members of a catalog, and the selection includes one."
            # A copy, since the base form shares `Meta.nullable_fields` across instances.
            self.nullable_fields = [name for name in self.nullable_fields if name != "catalog_zone"]
            return

        # A catalog holds zones from its own view only, so only a selection within one view can be added to one.
        view_ids = list(selection.order_by().values_list("dns_view_id", flat=True).distinct()[:2])
        if len(view_ids) > 1:
            catalog_zone.disabled = True
            catalog_zone.help_text = (
                "The selected zones are in more than one view, and a catalog zone holds zones from its own view "
                "only. Set null still removes them from their catalogs."
            )
        elif view_ids:
            catalog_zone.widget.add_query_param("dns_view", view_ids[0])

    def clean(self):
        """Refuse a catalog change the selection's views would make fail in the job."""
        cleaned_data = super().clean()
        if self.selection is None:
            return cleaned_data

        catalog_zone = cleaned_data.get("catalog_zone")
        if catalog_zone is not None:
            self._validate_catalog_view(catalog_zone, cleaned_data.get("dns_view"))

        return cleaned_data

    def _validate_catalog_view(self, catalog_zone, dns_view):
        """Refuse a catalog zone that some of the selected zones will not share a view with."""
        if dns_view is not None:
            outside = dns_view.pk != catalog_zone.dns_view_id
        else:
            outside = self.selection.exclude(dns_view_id=catalog_zone.dns_view_id).exists()

        if outside:
            self.add_error("catalog_zone", "The selected zones must be in the same view as the catalog zone.")


class DNSZoneBulkDeleteForm(ConfirmationForm):
    """Prepare zones for core's bulk delete job, which finds this form by its name."""

    def __init__(self, *args, delete_all=False, **kwargs):
        """Select the zones to delete, which may be omitted when deleting all."""
        super().__init__(*args, **kwargs)
        self.fields["pk"] = forms.ModelMultipleChoiceField(
            queryset=models.DNSZone.objects.all(), widget=forms.MultipleHiddenInput, required=not delete_all
        )

    def perform_pre_delete(self, queryset):
        """Withdraw member PTR records and clear system-managed records of the zones, unless something else protects them.

        Core's bulk delete collects the zones before it deletes them, so their system-managed records,
        which `DNSRecord.zone` protects, would refuse it. This runs before that delete, outside its
        transaction, so if anything else would refuse the delete (e.g. a catalog zone's members), the
        records are kept.
        """
        try:
            with transaction.atomic():
                queryset.prepare_for_delete()
                Collector(using=queryset.db).collect(list(queryset))
        except (ProtectedError, RestrictedError):
            pass


class AddToCatalogForm(BootstrapMixin, forms.Form):
    """Pick the catalog zone to add a zone to, from the catalog zones in the zone's view."""

    catalog_zone = DynamicModelChoiceField(
        queryset=models.DNSZone.objects.filter(type=DNSZoneTypeChoices.TYPE_CATALOG),
        query_params={"type": DNSZoneTypeChoices.TYPE_CATALOG},
        label="Catalog Zone",
    )
    member_label = forms.CharField(
        max_length=63,
        initial=models.catalog_member_label,
        label="Member Label",
        help_text="DNS label identifying the zone within the catalog zone.",
    )

    def __init__(self, *args, zone, **kwargs):
        """Offer only the catalog zones in `zone`'s view."""
        super().__init__(*args, **kwargs)
        self.fields["catalog_zone"].widget.add_query_param("dns_view", zone.dns_view_id)


class CatalogMemberAddForm(BootstrapMixin, forms.Form):
    """Pick an existing zone to add to a catalog zone, from the zones in the catalog zone's view."""

    zone = DynamicModelChoiceField(
        queryset=models.DNSZone.objects.exclude(type=DNSZoneTypeChoices.TYPE_CATALOG),
        query_params={
            "is_catalog_member": "False",
            "type__n": DNSZoneTypeChoices.TYPE_CATALOG,
            "can_change": "True",
        },
        label="Member Zone",
    )
    member_label = forms.CharField(
        max_length=63,
        initial=models.catalog_member_label,
        label="Member Label",
        help_text="DNS label identifying the zone within the catalog zone.",
    )

    def __init__(self, *args, catalog_zone, **kwargs):
        """Offer only the zones in `catalog_zone`'s view."""
        super().__init__(*args, **kwargs)
        self.fields["zone"].widget.add_query_param("dns_view", catalog_zone.dns_view_id)

    def clean_zone(self):
        """Refuse a zone already in a catalog, which this form would otherwise move."""
        zone = self.cleaned_data["zone"]
        if zone.catalog_zone_id is not None:
            raise forms.ValidationError(f"Zone {zone} is already a member of catalog zone {zone.catalog_zone}.")

        return zone


class DNSZoneFilterForm(NautobotFilterForm, TenancyFilterForm):
    """Filter form to filter searches."""

    q = forms.CharField(
        required=False,
        label="Search",
        help_text="Search within Name, Filename, SOA MNAME, and SOA RNAME.",
    )
    name = forms.CharField(required=False, label="Name")
    type = forms.MultipleChoiceField(
        required=False,
        choices=DNSZoneTypeChoices,
        widget=StaticSelect2Multiple(),
    )
    enabled = forms.NullBooleanField(
        required=False,
        widget=StaticSelect2(choices=BOOLEAN_WITH_BLANK_CHOICES),
    )
    filename = forms.CharField(required=False, label="Filename")
    parent = DynamicModelMultipleChoiceField(
        queryset=models.DNSZone.objects.all(),
        to_field_name="name",
        required=False,
        label="Parent zone",
    )
    has_parent = forms.NullBooleanField(
        required=False,
        label="Has parent zone",
        widget=StaticSelect2(choices=BOOLEAN_WITH_BLANK_CHOICES),
    )
    has_children = forms.NullBooleanField(
        required=False,
        label="Has child zones",
        widget=StaticSelect2(choices=BOOLEAN_WITH_BLANK_CHOICES),
    )
    catalog_zone = DynamicModelMultipleChoiceField(
        queryset=models.DNSZone.objects.filter(type=DNSZoneTypeChoices.TYPE_CATALOG),
        required=False,
        query_params={"type": DNSZoneTypeChoices.TYPE_CATALOG},
        to_field_name="name",
        label="Catalog Zone",
    )
    is_catalog_member = forms.NullBooleanField(
        required=False,
        label="Is a Catalog Member",
        widget=StaticSelect2(choices=BOOLEAN_WITH_BLANK_CHOICES),
    )
    model = models.DNSZone
    # Define the fields above for ordering and widget purposes
    fields = [
        "q",
        "name",
        "type",
        "enabled",
        "filename",
        "parent",
        "has_parent",
        "has_children",
        "catalog_zone",
        "is_catalog_member",
    ]


class NSRecordForm(EnabledBeforeDescriptionMixin, NautobotModelForm):
    """NSRecord creation/edit form."""

    class Meta:
        """Meta attributes."""

        model = models.NSRecord
        fields = "__all__"


class NSRecordBulkEditForm(TagsBulkEditFormMixin, NautobotBulkEditForm):
    """NSRecord bulk edit form."""

    pk = forms.ModelMultipleChoiceField(queryset=models.NSRecord.objects.all(), widget=forms.MultipleHiddenInput)
    description = forms.CharField(required=False)
    enabled = forms.NullBooleanField(required=False, widget=BulkEditNullBooleanSelect)

    class Meta:
        """Meta attributes."""

        nullable_fields = [
            "description",
        ]


class NSRecordFilterForm(NautobotFilterForm):
    """Filter form to filter searches."""

    q = forms.CharField(
        required=False,
        label="Search",
        help_text="Search within Name.",
    )
    name = forms.CharField(required=False, label="Name")
    server = forms.CharField(required=False, label="Server")
    zone = DynamicModelMultipleChoiceField(
        queryset=models.DNSZone.objects.all(),
        to_field_name="name",
        required=False,
        label="Zone",
    )
    enabled = forms.NullBooleanField(
        required=False,
        widget=StaticSelect2(choices=BOOLEAN_WITH_BLANK_CHOICES),
    )
    model = models.NSRecord
    # Define the fields above for ordering and widget purposes
    fields = [
        "q",
        "name",
        "enabled",
        "description",
    ]


class ARecordForm(EnabledBeforeDescriptionMixin, NautobotModelForm):
    """ARecord creation/edit form."""

    ip_address = DynamicModelChoiceField(
        queryset=IPAddress.objects.all(),
        required=True,
        query_params={"ip_version": IPAddressVersionChoices.VERSION_4},
        label="IP Address",
    )

    class Meta:
        """Meta attributes."""

        model = models.ARecord
        fields = "__all__"


class ARecordBulkEditForm(TagsBulkEditFormMixin, NautobotBulkEditForm):
    """ARecord bulk edit form."""

    pk = forms.ModelMultipleChoiceField(queryset=models.ARecord.objects.all(), widget=forms.MultipleHiddenInput)
    description = forms.CharField(required=False)
    enabled = forms.NullBooleanField(required=False, widget=BulkEditNullBooleanSelect)

    class Meta:
        """Meta attributes."""

        nullable_fields = [
            "description",
        ]


class ARecordFilterForm(NautobotFilterForm):
    """Filter form to filter searches."""

    q = forms.CharField(
        required=False,
        label="Search",
        help_text="Search within Name.",
    )
    name = forms.CharField(required=False, label="Name")
    zone = DynamicModelMultipleChoiceField(
        queryset=models.DNSZone.objects.all(),
        to_field_name="name",
        required=False,
        label="Zone",
    )
    enabled = forms.NullBooleanField(
        required=False,
        widget=StaticSelect2(choices=BOOLEAN_WITH_BLANK_CHOICES),
    )
    model = models.ARecord
    # Define the fields above for ordering and widget purposes
    fields = [
        "q",
        "name",
        "enabled",
        "description",
    ]


class AAAARecordForm(EnabledBeforeDescriptionMixin, NautobotModelForm):
    """AAAARecord creation/edit form."""

    ip_address = DynamicModelChoiceField(
        queryset=IPAddress.objects.all(),
        required=True,
        query_params={"ip_version": IPAddressVersionChoices.VERSION_6},
        label="IP Address",
    )

    class Meta:
        """Meta attributes."""

        model = models.AAAARecord
        fields = "__all__"


class AAAARecordBulkEditForm(TagsBulkEditFormMixin, NautobotBulkEditForm):
    """AAAARecord bulk edit form."""

    pk = forms.ModelMultipleChoiceField(queryset=models.AAAARecord.objects.all(), widget=forms.MultipleHiddenInput)
    description = forms.CharField(required=False)
    enabled = forms.NullBooleanField(required=False, widget=BulkEditNullBooleanSelect)

    class Meta:
        """Meta attributes."""

        nullable_fields = [
            "description",
        ]


class AAAARecordFilterForm(NautobotFilterForm):
    """Filter form to filter searches."""

    q = forms.CharField(
        required=False,
        label="Search",
        help_text="Search within Name.",
    )
    name = forms.CharField(required=False, label="Name")
    zone = DynamicModelMultipleChoiceField(
        queryset=models.DNSZone.objects.all(),
        to_field_name="name",
        required=False,
        label="Zone",
    )
    enabled = forms.NullBooleanField(
        required=False,
        widget=StaticSelect2(choices=BOOLEAN_WITH_BLANK_CHOICES),
    )
    model = models.AAAARecord
    # Define the fields above for ordering and widget purposes
    fields = [
        "q",
        "name",
        "enabled",
        "description",
    ]


class CNAMERecordForm(EnabledBeforeDescriptionMixin, NautobotModelForm):
    """CNAMERecord creation/edit form."""

    class Meta:
        """Meta attributes."""

        model = models.CNAMERecord
        fields = "__all__"


class CNAMERecordBulkEditForm(TagsBulkEditFormMixin, NautobotBulkEditForm):
    """CNAMERecord bulk edit form."""

    pk = forms.ModelMultipleChoiceField(queryset=models.CNAMERecord.objects.all(), widget=forms.MultipleHiddenInput)
    description = forms.CharField(required=False)
    enabled = forms.NullBooleanField(required=False, widget=BulkEditNullBooleanSelect)

    class Meta:
        """Meta attributes."""

        nullable_fields = [
            "description",
        ]


class CNAMERecordFilterForm(NautobotFilterForm):
    """Filter form to filter searches."""

    q = forms.CharField(
        required=False,
        label="Search",
        help_text="Search within Name.",
    )
    name = forms.CharField(required=False, label="Name")
    zone = DynamicModelMultipleChoiceField(
        queryset=models.DNSZone.objects.all(),
        to_field_name="name",
        required=False,
        label="Zone",
    )
    enabled = forms.NullBooleanField(
        required=False,
        widget=StaticSelect2(choices=BOOLEAN_WITH_BLANK_CHOICES),
    )
    model = models.CNAMERecord
    # Define the fields above for ordering and widget purposes
    fields = [
        "q",
        "name",
        "enabled",
        "description",
    ]


class MXRecordForm(EnabledBeforeDescriptionMixin, NautobotModelForm):
    """MXRecord creation/edit form."""

    class Meta:
        """Meta attributes."""

        model = models.MXRecord
        fields = "__all__"


class MXRecordBulkEditForm(TagsBulkEditFormMixin, NautobotBulkEditForm):
    """MXRecord bulk edit form."""

    pk = forms.ModelMultipleChoiceField(queryset=models.MXRecord.objects.all(), widget=forms.MultipleHiddenInput)
    description = forms.CharField(required=False)
    enabled = forms.NullBooleanField(required=False, widget=BulkEditNullBooleanSelect)

    class Meta:
        """Meta attributes."""

        nullable_fields = [
            "description",
        ]


class MXRecordFilterForm(NautobotFilterForm):
    """Filter form to filter searches."""

    q = forms.CharField(
        required=False,
        label="Search",
        help_text="Search within Name.",
    )
    name = forms.CharField(required=False, label="Name")
    zone = DynamicModelMultipleChoiceField(
        queryset=models.DNSZone.objects.all(),
        to_field_name="name",
        required=False,
        label="Zone",
    )
    enabled = forms.NullBooleanField(
        required=False,
        widget=StaticSelect2(choices=BOOLEAN_WITH_BLANK_CHOICES),
    )
    model = models.MXRecord
    # Define the fields above for ordering and widget purposes
    fields = [
        "q",
        "name",
        "enabled",
        "preference",
        "description",
    ]


class TXTRecordForm(EnabledBeforeDescriptionMixin, NautobotModelForm):
    """TXTRecord creation/edit form."""

    class Meta:
        """Meta attributes."""

        model = models.TXTRecord
        fields = "__all__"


class TXTRecordBulkEditForm(TagsBulkEditFormMixin, NautobotBulkEditForm):
    """TXTRecord bulk edit form."""

    pk = forms.ModelMultipleChoiceField(queryset=models.TXTRecord.objects.all(), widget=forms.MultipleHiddenInput)
    description = forms.CharField(required=False)
    enabled = forms.NullBooleanField(required=False, widget=BulkEditNullBooleanSelect)

    class Meta:
        """Meta attributes."""

        nullable_fields = [
            "description",
        ]


class TXTRecordFilterForm(NautobotFilterForm):
    """Filter form to filter searches."""

    q = forms.CharField(
        required=False,
        label="Search",
        help_text="Search within Name.",
    )
    name = forms.CharField(required=False, label="Name")
    zone = DynamicModelMultipleChoiceField(
        queryset=models.DNSZone.objects.all(),
        to_field_name="name",
        required=False,
        label="Zone",
    )
    enabled = forms.NullBooleanField(
        required=False,
        widget=StaticSelect2(choices=BOOLEAN_WITH_BLANK_CHOICES),
    )
    model = models.TXTRecord
    # Define the fields above for ordering and widget purposes
    fields = [
        "q",
        "name",
        "enabled",
        "description",
    ]


class PTRRecordForm(EnabledBeforeDescriptionMixin, NautobotModelForm):
    """PTRRecord creation/edit form."""

    class Meta:
        """Meta attributes."""

        model = models.PTRRecord
        fields = "__all__"


class PTRRecordBulkEditForm(TagsBulkEditFormMixin, NautobotBulkEditForm):
    """PTRRecord bulk edit form."""

    pk = forms.ModelMultipleChoiceField(queryset=models.PTRRecord.objects.all(), widget=forms.MultipleHiddenInput)
    description = forms.CharField(required=False)
    enabled = forms.NullBooleanField(required=False, widget=BulkEditNullBooleanSelect)

    class Meta:
        """Meta attributes."""

        nullable_fields = [
            "description",
        ]


class PTRRecordFilterForm(NautobotFilterForm):
    """Filter form to filter searches."""

    q = forms.CharField(
        required=False,
        label="Search",
        help_text="Search within Name.",
    )
    name = forms.CharField(required=False, label="Name")
    zone = DynamicModelMultipleChoiceField(
        queryset=models.DNSZone.objects.all(),
        to_field_name="name",
        required=False,
        label="Zone",
    )
    enabled = forms.NullBooleanField(
        required=False,
        widget=StaticSelect2(choices=BOOLEAN_WITH_BLANK_CHOICES),
    )
    model = models.PTRRecord
    # Define the fields above for ordering and widget purposes
    fields = [
        "q",
        "name",
        "enabled",
        "ttl",
        "comment",
        "description",
    ]


class SRVRecordForm(EnabledBeforeDescriptionMixin, NautobotModelForm):
    """SRVRecord creation/edit form."""

    class Meta:
        """Meta attributes."""

        model = models.SRVRecord
        fields = "__all__"


class SRVRecordBulkEditForm(TagsBulkEditFormMixin, NautobotBulkEditForm):
    """SRVRecord bulk edit form."""

    pk = forms.ModelMultipleChoiceField(queryset=models.SRVRecord.objects.all(), widget=forms.MultipleHiddenInput)
    description = forms.CharField(required=False)
    enabled = forms.NullBooleanField(required=False, widget=BulkEditNullBooleanSelect)

    class Meta:
        """Meta attributes."""

        nullable_fields = [
            "description",
        ]


class SRVRecordFilterForm(NautobotFilterForm):
    """Filter form to filter searches."""

    q = forms.CharField(
        required=False,
        label="Search",
        help_text="Search within Name.",
    )
    name = forms.CharField(required=False, label="Name")
    zone = DynamicModelMultipleChoiceField(
        queryset=models.DNSZone.objects.all(),
        to_field_name="name",
        required=False,
        label="Zone",
    )
    enabled = forms.NullBooleanField(
        required=False,
        widget=StaticSelect2(choices=BOOLEAN_WITH_BLANK_CHOICES),
    )
    model = models.SRVRecord
    # Define the fields above for ordering and widget purposes
    fields = [
        "q",
        "name",
        "enabled",
        "priority",
        "weight",
        "port",
        "target",
    ]
