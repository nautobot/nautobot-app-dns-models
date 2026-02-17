"""Forms for nautobot_dns_models."""

from django import forms
from nautobot.apps.forms import (
    DatePicker,
    DynamicModelChoiceField,
    DynamicModelMultipleChoiceField,
    NautobotBulkEditForm,
    NautobotFilterForm,
    NautobotModelForm,
    TagsBulkEditFormMixin,
)
from nautobot.ipam.models import Prefix
from nautobot.tenancy.forms import TenancyFilterForm, TenancyForm
from nautobot.tenancy.models import Tenant

from nautobot_dns_models import models

EXPIRATION_DATE_INPUT_FORMATS = ("%Y-%m-%d",)


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


class DNSZoneForm(NautobotModelForm, TenancyForm):
    """DNSZone creation/edit form."""

    expiration_date = forms.DateField(
        required=False,
        widget=DatePicker(),
        input_formats=EXPIRATION_DATE_INPUT_FORMATS,
    )

    class Meta:
        """Meta attributes."""

        model = models.DNSZone
        fields = "__all__"


class DNSZoneBulkEditForm(TagsBulkEditFormMixin, NautobotBulkEditForm):
    """DNSZone bulk edit form."""

    pk = forms.ModelMultipleChoiceField(queryset=models.DNSZone.objects.all(), widget=forms.MultipleHiddenInput)
    description = forms.CharField(required=False)
    dns_registrar = DynamicModelChoiceField(
        queryset=models.DNSRegistrar.objects.all(),
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
    tenant = DynamicModelChoiceField(
        queryset=Tenant.objects.all(),
        required=False,
    )

    class Meta:
        """Meta attributes."""

        nullable_fields = [
            "description",
            "dns_registrar",
            "expiration_date",
            "renewal_term_months",
            "tenant",
        ]


class DNSZoneFilterForm(NautobotFilterForm, TenancyFilterForm):
    """Filter form to filter searches."""

    q = forms.CharField(
        required=False,
        label="Search",
        help_text="Search within Name, Filename, Registrar, SOA MNAME, and SOA RNAME.",
    )
    name = forms.CharField(required=False, label="Name")
    filename = forms.CharField(required=False, label="Filename")
    dns_registrar = DynamicModelChoiceField(
        queryset=models.DNSRegistrar.objects.all(),
        required=False,
        label="Registrar",
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
    model = models.DNSZone
    # Define the fields above for ordering and widget purposes
    fields = [
        "q",
        "name",
        "filename",
        "dns_registrar",
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


class NSRecordForm(NautobotModelForm):
    """NSRecord creation/edit form."""

    class Meta:
        """Meta attributes."""

        model = models.NSRecord
        fields = "__all__"


class NSRecordBulkEditForm(TagsBulkEditFormMixin, NautobotBulkEditForm):
    """NSRecord bulk edit form."""

    pk = forms.ModelMultipleChoiceField(queryset=models.NSRecord.objects.all(), widget=forms.MultipleHiddenInput)
    description = forms.CharField(required=False)

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
    model = models.NSRecord
    # Define the fields above for ordering and widget purposes
    fields = [
        "q",
        "name",
        "description",
    ]


class ARecordForm(NautobotModelForm):
    """ARecord creation/edit form."""

    class Meta:
        """Meta attributes."""

        model = models.ARecord
        fields = "__all__"


class ARecordBulkEditForm(TagsBulkEditFormMixin, NautobotBulkEditForm):
    """ARecord bulk edit form."""

    pk = forms.ModelMultipleChoiceField(queryset=models.ARecord.objects.all(), widget=forms.MultipleHiddenInput)
    description = forms.CharField(required=False)

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
    zone = forms.CharField(required=False, label="Zone")
    model = models.ARecord
    # Define the fields above for ordering and widget purposes
    fields = [
        "q",
        "name",
        "description",
    ]


class AAAARecordForm(NautobotModelForm):
    """AAAARecord creation/edit form."""

    class Meta:
        """Meta attributes."""

        model = models.AAAARecord
        fields = "__all__"


class AAAARecordBulkEditForm(TagsBulkEditFormMixin, NautobotBulkEditForm):
    """AAAARecord bulk edit form."""

    pk = forms.ModelMultipleChoiceField(queryset=models.AAAARecord.objects.all(), widget=forms.MultipleHiddenInput)
    description = forms.CharField(required=False)

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
    model = models.AAAARecord
    # Define the fields above for ordering and widget purposes
    fields = [
        "q",
        "name",
        "description",
    ]


class CNAMERecordForm(NautobotModelForm):
    """CNAMERecord creation/edit form."""

    class Meta:
        """Meta attributes."""

        model = models.CNAMERecord
        fields = "__all__"


class CNAMERecordBulkEditForm(TagsBulkEditFormMixin, NautobotBulkEditForm):
    """CNAMERecord bulk edit form."""

    pk = forms.ModelMultipleChoiceField(queryset=models.CNAMERecord.objects.all(), widget=forms.MultipleHiddenInput)
    description = forms.CharField(required=False)

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
    model = models.CNAMERecord
    # Define the fields above for ordering and widget purposes
    fields = [
        "q",
        "name",
        "description",
    ]


class MXRecordForm(NautobotModelForm):
    """MXRecord creation/edit form."""

    class Meta:
        """Meta attributes."""

        model = models.MXRecord
        fields = "__all__"


class MXRecordBulkEditForm(TagsBulkEditFormMixin, NautobotBulkEditForm):
    """MXRecord bulk edit form."""

    pk = forms.ModelMultipleChoiceField(queryset=models.MXRecord.objects.all(), widget=forms.MultipleHiddenInput)
    description = forms.CharField(required=False)

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
    model = models.MXRecord
    # Define the fields above for ordering and widget purposes
    fields = [
        "q",
        "name",
        "preference",
        "description",
    ]


class TXTRecordForm(NautobotModelForm):
    """TXTRecord creation/edit form."""

    class Meta:
        """Meta attributes."""

        model = models.TXTRecord
        fields = "__all__"


class TXTRecordBulkEditForm(TagsBulkEditFormMixin, NautobotBulkEditForm):
    """TXTRecord bulk edit form."""

    pk = forms.ModelMultipleChoiceField(queryset=models.TXTRecord.objects.all(), widget=forms.MultipleHiddenInput)
    description = forms.CharField(required=False)

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
    model = models.TXTRecord
    # Define the fields above for ordering and widget purposes
    fields = [
        "q",
        "name",
        "description",
    ]


class PTRRecordForm(NautobotModelForm):
    """PTRRecord creation/edit form."""

    class Meta:
        """Meta attributes."""

        model = models.PTRRecord
        fields = "__all__"


class PTRRecordBulkEditForm(TagsBulkEditFormMixin, NautobotBulkEditForm):
    """PTRRecord bulk edit form."""

    pk = forms.ModelMultipleChoiceField(queryset=models.PTRRecord.objects.all(), widget=forms.MultipleHiddenInput)
    description = forms.CharField(required=False)

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
    model = models.PTRRecord
    # Define the fields above for ordering and widget purposes
    fields = [
        "q",
        "name",
        "ttl",
        "comment",
        "description",
    ]


class SRVRecordForm(NautobotModelForm):
    """SRVRecord creation/edit form."""

    class Meta:
        """Meta attributes."""

        model = models.SRVRecord
        fields = "__all__"


class SRVRecordBulkEditForm(TagsBulkEditFormMixin, NautobotBulkEditForm):
    """SRVRecord bulk edit form."""

    pk = forms.ModelMultipleChoiceField(queryset=models.SRVRecord.objects.all(), widget=forms.MultipleHiddenInput)
    description = forms.CharField(required=False)

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
    model = models.SRVRecord
    # Define the fields above for ordering and widget purposes
    fields = [
        "q",
        "name",
        "priority",
        "weight",
        "port",
        "target",
    ]
