"""Forms for nautobot_dns_models."""

from django import forms
from nautobot.apps.forms import (
    NautobotBulkEditForm,
    NautobotModelForm,
    TagsBulkEditFormMixin,
)
from nautobot.extras.forms import NautobotFilterForm

from nautobot_dns_models import models


class DNSZoneForm(NautobotModelForm):
    """DNSZone creation/edit form."""

    class Meta:
        """Meta attributes."""

        model = models.DNSZone
        fields = "__all__"


class DNSZoneBulkEditForm(TagsBulkEditFormMixin, NautobotBulkEditForm):
    """DNSZone bulk edit form."""

    pk = forms.ModelMultipleChoiceField(queryset=models.DNSZone.objects.all(), widget=forms.MultipleHiddenInput)
    description = forms.CharField(required=False)

    class Meta:
        """Meta attributes."""

        nullable_fields = [
            "description",
        ]


class DNSZoneFilterForm(NautobotFilterForm):
    """Filter form to filter searches."""

    q = forms.CharField(
        required=False,
        label="Search",
        help_text="Search within Name.",
    )
    name = forms.CharField(required=False, label="Name")
    model = models.DNSZone
    # Define the fields above for ordering and widget purposes
    fields = [
        "q",
        "name",
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
