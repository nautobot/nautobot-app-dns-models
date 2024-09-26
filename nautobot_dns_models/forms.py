"""Forms for nautobot_dns_models."""

from django import forms
from nautobot.core.forms import (
    BootstrapMixin,
    BulkEditForm,
)

from nautobot_dns_models import models


class DNSZoneModelForm(BootstrapMixin, forms.ModelForm):
    """DnsZoneModel creation/edit form."""

    class Meta:
        """Meta attributes."""

        model = models.DNSZoneModel
        fields = [
            "name",
            "description",
            "filename",
            "soa_mname",
            "soa_rname",
            "soa_refresh",
            "soa_retry",
            "soa_expire",
            "soa_serial",
            "soa_minimum",
        ]


class DNSZoneModelBulkCreateForm(BootstrapMixin, forms.ModelForm):
    """DnsZoneModel bulk create form."""

    class Meta:
        """Meta attributes."""

        model = models.DNSZoneModel
        fields = [
            "name",
            "description",
        ]


class DNSZoneModelBulkEditForm(BootstrapMixin, BulkEditForm):
    """DnsZoneModel bulk edit form."""

    pk = forms.ModelMultipleChoiceField(queryset=models.DNSZoneModel.objects.all(), widget=forms.MultipleHiddenInput)
    description = forms.CharField(required=False)

    class Meta:
        """Meta attributes."""

        nullable_fields = [
            "description",
        ]


class DNSZoneModelFilterForm(BootstrapMixin, forms.ModelForm):
    """Filter form to filter searches."""

    q = forms.CharField(
        required=False,
        label="Search",
        help_text="Search within Name.",
    )
    name = forms.CharField(required=False, label="Name")

    class Meta:
        """Meta attributes."""

        model = models.DNSZoneModel
        # Define the fields above for ordering and widget purposes
        fields = [
            "q",
            "name",
        ]


class NSRecordModelForm(BootstrapMixin, forms.ModelForm):
    """NSRecordModel creation/edit form."""

    class Meta:
        """Meta attributes."""

        model = models.NSRecordModel
        fields = [
            "name",
            "server",
            "zone",
            "description",
        ]


class NSRecordModelBulkEditForm(BootstrapMixin, BulkEditForm):
    """NSRecordModel bulk edit form."""

    pk = forms.ModelMultipleChoiceField(queryset=models.NSRecordModel.objects.all(), widget=forms.MultipleHiddenInput)
    description = forms.CharField(required=False)

    class Meta:
        """Meta attributes."""

        nullable_fields = [
            "description",
        ]


class NSRecordModelFilterForm(BootstrapMixin, forms.ModelForm):
    """Filter form to filter searches."""

    q = forms.CharField(
        required=False,
        label="Search",
        help_text="Search within Name.",
    )
    name = forms.CharField(required=False, label="Name")
    server = forms.CharField(required=False, label="Server")

    class Meta:
        """Meta attributes."""

        model = models.NSRecordModel
        # Define the fields above for ordering and widget purposes
        fields = [
            "q",
            "name",
            "description",
        ]


class ARecordModelForm(BootstrapMixin, forms.ModelForm):
    """ARecordModel creation/edit form."""

    class Meta:
        """Meta attributes."""

        model = models.ARecordModel
        fields = [
            "name",
            "address",
            "ttl",
            "zone",
            "comment",
            "description",
        ]


class ARecordModelBulkEditForm(BootstrapMixin, BulkEditForm):
    """ARecordModel bulk edit form."""

    pk = forms.ModelMultipleChoiceField(queryset=models.ARecordModel.objects.all(), widget=forms.MultipleHiddenInput)
    description = forms.CharField(required=False)

    class Meta:
        """Meta attributes."""

        nullable_fields = [
            "description",
        ]


class ARecordModelFilterForm(BootstrapMixin, forms.ModelForm):
    """Filter form to filter searches."""

    q = forms.CharField(
        required=False,
        label="Search",
        help_text="Search within Name.",
    )
    name = forms.CharField(required=False, label="Name")
    zone = forms.CharField(required=False, label="Zone")

    class Meta:
        """Meta attributes."""

        model = models.ARecordModel
        # Define the fields above for ordering and widget purposes
        fields = [
            "q",
            "name",
            "description",
        ]


class AAAARecordModelForm(BootstrapMixin, forms.ModelForm):
    """AAAARecordModel creation/edit form."""

    class Meta:
        """Meta attributes."""

        model = models.AAAARecordModel
        fields = [
            "name",
            "address",
            "ttl",
            "zone",
            "comment",
            "description",
        ]


class AAAARecordModelBulkEditForm(BootstrapMixin, BulkEditForm):
    """AAAARecordModel bulk edit form."""

    pk = forms.ModelMultipleChoiceField(queryset=models.AAAARecordModel.objects.all(), widget=forms.MultipleHiddenInput)
    description = forms.CharField(required=False)

    class Meta:
        """Meta attributes."""

        nullable_fields = [
            "description",
        ]


class AAAARecordModelFilterForm(BootstrapMixin, forms.ModelForm):
    """Filter form to filter searches."""

    q = forms.CharField(
        required=False,
        label="Search",
        help_text="Search within Name.",
    )
    name = forms.CharField(required=False, label="Name")

    class Meta:
        """Meta attributes."""

        model = models.AAAARecordModel
        # Define the fields above for ordering and widget purposes
        fields = [
            "q",
            "name",
            "description",
        ]


class CNAMERecordModelForm(BootstrapMixin, forms.ModelForm):
    """CNAMERecordModel creation/edit form."""

    class Meta:
        """Meta attributes."""

        model = models.CNAMERecordModel
        fields = [
            "name",
            "alias",
            "zone",
            "description",
        ]


class CNAMERecordModelBulkEditForm(BootstrapMixin, BulkEditForm):
    """CNAMERecordModel bulk edit form."""

    pk = forms.ModelMultipleChoiceField(
        queryset=models.CNAMERecordModel.objects.all(), widget=forms.MultipleHiddenInput
    )
    description = forms.CharField(required=False)

    class Meta:
        """Meta attributes."""

        nullable_fields = [
            "description",
        ]


class CNAMERecordModelFilterForm(BootstrapMixin, forms.ModelForm):
    """Filter form to filter searches."""

    q = forms.CharField(
        required=False,
        label="Search",
        help_text="Search within Name.",
    )
    name = forms.CharField(required=False, label="Name")

    class Meta:
        """Meta attributes."""

        model = models.CNAMERecordModel
        # Define the fields above for ordering and widget purposes
        fields = [
            "q",
            "name",
            "description",
        ]


class MXRecordModelForm(BootstrapMixin, forms.ModelForm):
    """MXRecordModel creation/edit form."""

    class Meta:
        """Meta attributes."""

        model = models.MXRecordModel
        fields = [
            "name",
            "preference",
            "mail_server",
            "zone",
            "description",
        ]


class MXRecordModelBulkEditForm(BootstrapMixin, BulkEditForm):
    """MXRecordModel bulk edit form."""

    pk = forms.ModelMultipleChoiceField(queryset=models.MXRecordModel.objects.all(), widget=forms.MultipleHiddenInput)
    description = forms.CharField(required=False)

    class Meta:
        """Meta attributes."""

        nullable_fields = [
            "description",
        ]


class MXRecordModelFilterForm(BootstrapMixin, forms.ModelForm):
    """Filter form to filter searches."""

    q = forms.CharField(
        required=False,
        label="Search",
        help_text="Search within Name.",
    )
    name = forms.CharField(required=False, label="Name")

    class Meta:
        """Meta attributes."""

        model = models.MXRecordModel
        # Define the fields above for ordering and widget purposes
        fields = [
            "q",
            "name",
            "preference",
            "description",
        ]


class TXTRecordModelForm(BootstrapMixin, forms.ModelForm):
    """TXTRecordModel creation/edit form."""

    class Meta:
        """Meta attributes."""

        model = models.TXTRecordModel
        fields = [
            "name",
            "text",
            "zone",
            "description",
        ]


class TXTRecordModelBulkEditForm(BootstrapMixin, BulkEditForm):
    """TXTRecordModel bulk edit form."""

    pk = forms.ModelMultipleChoiceField(queryset=models.TXTRecordModel.objects.all(), widget=forms.MultipleHiddenInput)
    description = forms.CharField(required=False)

    class Meta:
        """Meta attributes."""

        nullable_fields = [
            "description",
        ]


class TXTRecordModelFilterForm(BootstrapMixin, forms.ModelForm):
    """Filter form to filter searches."""

    q = forms.CharField(
        required=False,
        label="Search",
        help_text="Search within Name.",
    )
    name = forms.CharField(required=False, label="Name")

    class Meta:
        """Meta attributes."""

        model = models.TXTRecordModel
        # Define the fields above for ordering and widget purposes
        fields = [
            "q",
            "name",
            "description",
        ]


class PTRRecordModelForm(BootstrapMixin, forms.ModelForm):
    """PTRRecordModel creation/edit form."""

    class Meta:
        """Meta attributes."""

        model = models.PTRRecordModel
        fields = [
            "name",
            "ptrdname",
            "ttl",
            "zone",
            "comment",
            "description",
        ]


class PTRRecordModelBulkEditForm(BootstrapMixin, BulkEditForm):
    """PTRRecordModel bulk edit form."""

    pk = forms.ModelMultipleChoiceField(queryset=models.PTRRecordModel.objects.all(), widget=forms.MultipleHiddenInput)
    description = forms.CharField(required=False)

    class Meta:
        """Meta attributes."""

        nullable_fields = [
            "description",
        ]


class PTRRecordModelFilterForm(BootstrapMixin, forms.ModelForm):
    """Filter form to filter searches."""

    q = forms.CharField(
        required=False,
        label="Search",
        help_text="Search within Name.",
    )
    name = forms.CharField(required=False, label="Name")

    class Meta:
        """Meta attributes."""

        model = models.PTRRecordModel
        # Define the fields above for ordering and widget purposes
        fields = [
            "q",
            "name",
            "description",
        ]
