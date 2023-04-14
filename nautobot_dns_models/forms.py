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
