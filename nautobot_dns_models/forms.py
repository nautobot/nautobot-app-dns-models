"""Forms for nautobot_dns_models."""

from django import forms
from nautobot.apps.forms import NautobotBulkEditForm, NautobotFilterForm, NautobotModelForm, TagsBulkEditFormMixin

from nautobot_dns_models import models


class DnsZoneModelForm(NautobotModelForm):  # pylint: disable=too-many-ancestors
    """DnsZoneModel creation/edit form."""

    class Meta:
        """Meta attributes."""

        model = models.DnsZoneModel
        fields = [
            "name",
            "description",
        ]


class DnsZoneModelBulkEditForm(TagsBulkEditFormMixin, NautobotBulkEditForm):  # pylint: disable=too-many-ancestors
    """DnsZoneModel bulk edit form."""

    pk = forms.ModelMultipleChoiceField(queryset=models.DnsZoneModel.objects.all(), widget=forms.MultipleHiddenInput)
    description = forms.CharField(required=False)

    class Meta:
        """Meta attributes."""

        nullable_fields = [
            "description",
        ]


class DnsZoneModelFilterForm(NautobotFilterForm):
    """Filter form to filter searches."""

    model = models.DnsZoneModel
    field_order = ["q", "name"]

    q = forms.CharField(
        required=False,
        label="Search",
        help_text="Search within Name or Slug.",
    )
    name = forms.CharField(required=False, label="Name")
