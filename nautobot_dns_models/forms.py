"""Forms for nautobot_dns_models."""

from django import forms
from nautobot.apps.forms import (
    BootstrapMixin,
    BulkEditNullBooleanSelect,
    DatePicker,
    DynamicModelChoiceField,
    DynamicModelMultipleChoiceField,
    NautobotBulkEditForm,
    NautobotFilterForm,
    NautobotModelForm,
    StaticSelect2,
    StaticSelect2Multiple,
    TagsBulkEditFormMixin,
    add_blank_choice,
)

# This should be updated after https://github.com/nautobot/nautobot/issues/9302 is resolved
from nautobot.core.forms.constants import BOOLEAN_WITH_BLANK_CHOICES
from nautobot.extras.models import Status
from nautobot.ipam.choices import IPAddressVersionChoices
from nautobot.ipam.models import IPAddress, Prefix
from nautobot.tenancy.forms import TenancyFilterForm, TenancyForm
from nautobot.tenancy.models import Tenant

from nautobot_dns_models import models
from nautobot_dns_models.choices import DNSForwardingRuleActionChoices

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
    url = forms.URLField(required=False)
    account_number = forms.CharField(required=False)

    class Meta:
        """Meta attributes."""

        nullable_fields = [
            "url",
            "account_number",
        ]


class DNSRegistrarFilterForm(NautobotFilterForm):
    """Filter form to filter searches."""

    q = forms.CharField(
        required=False,
        label="Search",
        help_text="Search within Name, URL, and Account Number.",
    )
    name = forms.CharField(required=False, label="Name")
    url = forms.CharField(required=False, label="URL")
    account_number = forms.CharField(required=False, label="Account Number")
    model = models.DNSRegistrar
    fields = [
        "q",
        "name",
        "url",
        "account_number",
    ]


class DNSRegistrationForm(NautobotModelForm):
    """DNSRegistration creation/edit form."""

    expiration_date = forms.DateField(
        required=False,
        widget=DatePicker(),
        input_formats=EXPIRATION_DATE_INPUT_FORMATS,
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


class DNSZoneForm(EnabledBeforeDescriptionMixin, NautobotModelForm, TenancyForm):
    """DNSZone creation/edit form."""

    dns_view = DynamicModelChoiceField(
        queryset=models.DNSView.objects.all(),
        required=True,
        label="View",
    )

    class Meta:
        """Meta attributes."""

        model = models.DNSZone
        fields = "__all__"


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
    enabled = forms.NullBooleanField(required=False, widget=BulkEditNullBooleanSelect)

    class Meta:
        """Meta attributes."""

        nullable_fields = [
            "description",
            "tenant",
        ]


class DNSZoneFilterForm(NautobotFilterForm, TenancyFilterForm):
    """Filter form to filter searches."""

    q = forms.CharField(
        required=False,
        label="Search",
        help_text="Search within Name, Filename, SOA MNAME, and SOA RNAME.",
    )
    name = forms.CharField(required=False, label="Name")
    enabled = forms.NullBooleanField(
        required=False,
        widget=StaticSelect2(choices=BOOLEAN_WITH_BLANK_CHOICES),
    )
    filename = forms.CharField(required=False, label="Filename")
    parent_zone = DynamicModelMultipleChoiceField(
        queryset=models.DNSZone.objects.all(),
        required=False,
        label="Parent Zone",
    )
    model = models.DNSZone
    # Define the fields above for ordering and widget purposes
    fields = [
        "q",
        "name",
        "enabled",
        "filename",
        "parent_zone",
    ]


class DNSForwardingRuleForm(NautobotModelForm, TenancyForm):
    """DNSForwardingRule creation/edit form."""

    dns_view = DynamicModelChoiceField(
        queryset=models.DNSView.objects.all(),
        required=True,
        label="View",
    )

    class Meta:
        """Meta attributes."""

        model = models.DNSForwardingRule
        fields = "__all__"


class DNSForwardingRuleIPAddressAssignmentForm(BootstrapMixin, forms.ModelForm):
    """Form for one forwarder row in the DNSForwardingRule create/edit page."""

    # None of these are required in HTML, so the blank rows the page starts with do not block submitting it.
    # Rows added with "Add another forwarder" start out empty, so an empty port or weight gets the model default.
    ip_address = DynamicModelChoiceField(queryset=IPAddress.objects.all(), required=False, label="IP Address")
    port = forms.IntegerField(required=False, initial=53, min_value=1, max_value=65535, label="Port")
    weight = forms.IntegerField(required=False, initial=100, min_value=0, max_value=32767, label="Weight")

    class Meta:
        """Meta attributes."""

        model = models.DNSForwardingRuleIPAddressAssignment
        fields = ["ip_address", "port", "weight"]

    def has_changed(self):
        """Treat new rows without an IP address as unchanged, so the formset skips them."""
        if not self.instance.present_in_database and not self.data.get(self.add_prefix("ip_address")):
            return False
        return super().has_changed()

    def clean_ip_address(self):
        """Require an IP address on every row that is kept."""
        ip_address = self.cleaned_data.get("ip_address")
        if ip_address is None:
            raise forms.ValidationError("An IP address is required.")
        return ip_address

    def _clean_with_default(self, field_name):
        value = self.cleaned_data.get(field_name)
        if value is None:
            return models.DNSForwardingRuleIPAddressAssignment._meta.get_field(field_name).default
        return value

    def clean_port(self):
        """Default an empty port to 53."""
        return self._clean_with_default("port")

    def clean_weight(self):
        """Default an empty weight to 100."""
        return self._clean_with_default("weight")


DNSForwardingRuleIPAddressAssignmentFormSet = forms.inlineformset_factory(
    parent_model=models.DNSForwardingRule,
    model=models.DNSForwardingRuleIPAddressAssignment,
    form=DNSForwardingRuleIPAddressAssignmentForm,
    fk_name="forwarding_rule",
    extra=3,
)


class DNSForwardingRuleBulkEditForm(TagsBulkEditFormMixin, NautobotBulkEditForm):
    """DNSForwardingRule bulk edit form."""

    pk = forms.ModelMultipleChoiceField(
        queryset=models.DNSForwardingRule.objects.all(), widget=forms.MultipleHiddenInput
    )
    dns_view = DynamicModelChoiceField(
        queryset=models.DNSView.objects.all(),
        required=False,
        label="View",
    )
    action = forms.ChoiceField(
        choices=add_blank_choice(DNSForwardingRuleActionChoices),
        required=False,
        widget=StaticSelect2(),
    )
    enabled = forms.NullBooleanField(required=False, widget=BulkEditNullBooleanSelect)
    description = forms.CharField(required=False)
    tenant = DynamicModelChoiceField(
        queryset=Tenant.objects.all(),
        required=False,
    )

    class Meta:
        """Meta attributes."""

        nullable_fields = [
            "description",
            "tenant",
        ]


class DNSForwardingRuleFilterForm(NautobotFilterForm, TenancyFilterForm):
    """Filter form for DNSForwardingRule searches."""

    q = forms.CharField(
        required=False,
        label="Search",
        help_text="Search within Name and Description.",
    )
    name = forms.CharField(required=False, label="Name")
    dns_view = DynamicModelMultipleChoiceField(
        queryset=models.DNSView.objects.all(),
        required=False,
        label="View",
    )
    action = forms.MultipleChoiceField(
        choices=DNSForwardingRuleActionChoices,
        required=False,
        widget=StaticSelect2Multiple(),
    )
    enabled = forms.NullBooleanField(
        required=False,
        widget=StaticSelect2(choices=BOOLEAN_WITH_BLANK_CHOICES),
    )
    model = models.DNSForwardingRule
    # Define the fields above for ordering and widget purposes
    fields = [
        "q",
        "name",
        "dns_view",
        "action",
        "enabled",
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
