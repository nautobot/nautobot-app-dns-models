"""Forms for nautobot_dns_models."""

from django import forms
from nautobot.core.forms import (
    BootstrapMixin,
    BulkEditForm,
    SlugField,
)

from nautobot_dns_models import models


class DNSZoneModelForm(BootstrapMixin, forms.ModelForm):
    """DnsZoneModel creation/edit form."""

    slug = SlugField()

    class Meta:
        """Meta attributes."""

        model = models.DNSZoneModel
        fields = [
            "name",
            "slug",
            "description",
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

    slug = SlugField()

    class Meta:
        """Meta attributes."""

        model = models.DNSZoneModel
        fields = [
            "name",
            "slug",
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
        help_text="Search within Name or Slug.",
    )
    name = forms.CharField(required=False, label="Name")
    slug = forms.CharField(required=False, label="Slug")

    class Meta:
        """Meta attributes."""

        model = models.DNSZoneModel
        # Define the fields above for ordering and widget purposes
        fields = [
            "q",
            "name",
            "slug",
        ]


class NSRecordModelForm(BootstrapMixin, forms.ModelForm):
    """NSRecordModel creation/edit form."""

    slug = SlugField()

    class Meta:
        """Meta attributes."""

        model = models.NSRecordModel
        fields = [
            "name",
            "server",
            "slug",
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
        help_text="Search within Name or Slug.",
    )
    name = forms.CharField(required=False, label="Name")
    slug = forms.CharField(required=False, label="Slug")

    class Meta:
        """Meta attributes."""

        model = models.NSRecordModel
        # Define the fields above for ordering and widget purposes
        fields = [
            "q",
            "name",
            "slug",
            "description",
        ]


class ARecordModelForm(BootstrapMixin, forms.ModelForm):
    """ARecordModel creation/edit form."""

    slug = SlugField()

    class Meta:
        """Meta attributes."""

        model = models.ARecordModel
        fields = [
            "name",
            "slug",
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
        help_text="Search within Name or Slug.",
    )
    name = forms.CharField(required=False, label="Name")
    slug = forms.CharField(required=False, label="Slug")
    zone = forms.CharField(required=False, label="Zone")

    class Meta:
        """Meta attributes."""

        model = models.ARecordModel
        # Define the fields above for ordering and widget purposes
        fields = [
            "q",
            "name",
            "slug",
            "description",
        ]


class AAAARecordModelForm(BootstrapMixin, forms.ModelForm):
    """AAAARecordModel creation/edit form."""

    slug = SlugField()

    class Meta:
        """Meta attributes."""

        model = models.AAAARecordModel
        fields = [
            "name",
            "slug",
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
        help_text="Search within Name or Slug.",
    )
    name = forms.CharField(required=False, label="Name")
    slug = forms.CharField(required=False, label="Slug")

    class Meta:
        """Meta attributes."""

        model = models.AAAARecordModel
        # Define the fields above for ordering and widget purposes
        fields = [
            "q",
            "name",
            "slug",
            "description",
        ]


class CNAMERecordModelForm(BootstrapMixin, forms.ModelForm):
    """CNAMERecordModel creation/edit form."""

    slug = SlugField()

    class Meta:
        """Meta attributes."""

        model = models.CNAMERecordModel
        fields = [
            "name",
            "slug",
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
        help_text="Search within Name or Slug.",
    )
    name = forms.CharField(required=False, label="Name")
    slug = forms.CharField(required=False, label="Slug")

    class Meta:
        """Meta attributes."""

        model = models.CNAMERecordModel
        # Define the fields above for ordering and widget purposes
        fields = [
            "q",
            "name",
            "slug",
            "description",
        ]


class MXRecordModelForm(BootstrapMixin, forms.ModelForm):
    """MXRecordModel creation/edit form."""

    slug = SlugField()

    class Meta:
        """Meta attributes."""

        model = models.MXRecordModel
        fields = [
            "name",
            "slug",
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
        help_text="Search within Name or Slug.",
    )
    name = forms.CharField(required=False, label="Name")
    slug = forms.CharField(required=False, label="Slug")

    class Meta:
        """Meta attributes."""

        model = models.MXRecordModel
        # Define the fields above for ordering and widget purposes
        fields = [
            "q",
            "name",
            "slug",
            "preference",
            "description",
        ]


class TXTRecordModelForm(BootstrapMixin, forms.ModelForm):
    """TXTRecordModel creation/edit form."""

    slug = SlugField()

    class Meta:
        """Meta attributes."""

        model = models.TXTRecordModel
        fields = [
            "name",
            "slug",
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
        help_text="Search within Name or Slug.",
    )
    name = forms.CharField(required=False, label="Name")
    slug = forms.CharField(required=False, label="Slug")

    class Meta:
        """Meta attributes."""

        model = models.TXTRecordModel
        # Define the fields above for ordering and widget purposes
        fields = [
            "q",
            "name",
            "slug",
            "description",
        ]


class PTRRecordModelForm(BootstrapMixin, forms.ModelForm):
    """PTRRecordModel creation/edit form."""

    slug = SlugField()

    class Meta:
        """Meta attributes."""

        model = models.PTRRecordModel
        fields = [
            "name",
            "slug",
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
        help_text="Search within Name or Slug.",
    )
    name = forms.CharField(required=False, label="Name")
    slug = forms.CharField(required=False, label="Slug")

    class Meta:
        """Meta attributes."""

        model = models.PTRRecordModel
        # Define the fields above for ordering and widget purposes
        fields = [
            "q",
            "name",
            "slug",
            "description",
        ]
