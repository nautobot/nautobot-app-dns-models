"""Forms for nautobot_dns_models."""
from django import forms
from nautobot.utilities.forms import (
    BootstrapMixin,
    BulkEditForm,
    SlugField,
)

from nautobot_dns_models import models


class DnsZoneModelForm(BootstrapMixin, forms.ModelForm):
    """DnsZoneModel creation/edit form."""

    slug = SlugField()

    class Meta:
        """Meta attributes."""

        model = models.DnsZoneModel
        fields = [
            "name",
            "slug",
            "description",
        ]


class DnsZoneModelBulkCreateForm(BootstrapMixin, forms.ModelForm):
    """DnsZoneModel bulk create form."""

    slug = SlugField()

    class Meta:
        """Meta attributes."""

        model = models.DnsZoneModel
        fields = [
            "name",
            "slug",
            "description",
        ]


class DnsZoneModelBulkEditForm(BootstrapMixin, BulkEditForm):
    """DnsZoneModel bulk edit form."""

    pk = forms.ModelMultipleChoiceField(queryset=models.DnsZoneModel.objects.all(), widget=forms.MultipleHiddenInput)
    description = forms.CharField(required=False)

    class Meta:
        """Meta attributes."""

        nullable_fields = [
            "description",
        ]


class DnsZoneModelFilterForm(BootstrapMixin, forms.ModelForm):
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

        model = models.DnsZoneModel
        # Define the fields above for ordering and widget purposes
        fields = [
            "q",
            "name",
            "slug",
            "description",
        ]


class NSRecordModelForm(BootstrapMixin, forms.ModelForm):
    """NSRecordModel creation/edit form."""

    slug = SlugField()

    class Meta:
        """Meta attributes."""

        model = models.NSRecordModel
        fields = [
            "name",
            "slug",
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
            "alias",
            "slug",
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
