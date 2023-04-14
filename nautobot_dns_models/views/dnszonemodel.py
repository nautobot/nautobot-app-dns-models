"""Views for DnsZoneModel."""

from nautobot.core.views import generic

from nautobot_dns_models import filters, forms, models, tables


class DnsZoneModelListView(generic.ObjectListView):
    """List view."""

    queryset = models.DnsZoneModel.objects.all()
    # These aren't needed for simple models, but we can always add
    # this search functionality.
    filterset = filters.DnsZoneModelFilterSet
    filterset_form = forms.DnsZoneModelFilterForm
    table = tables.DnsZoneModelTable

    # Option for modifying the top right buttons on the list view:
    # action_buttons = ("add", "import", "export")


class DnsZoneModelView(generic.ObjectView):
    """Detail view."""

    queryset = models.DnsZoneModel.objects.all()


class DnsZoneModelCreateView(generic.ObjectEditView):
    """Create view."""

    model = models.DnsZoneModel
    queryset = models.DnsZoneModel.objects.all()
    model_form = forms.DnsZoneModelForm


class DnsZoneModelDeleteView(generic.ObjectDeleteView):
    """Delete view."""

    model = models.DnsZoneModel
    queryset = models.DnsZoneModel.objects.all()


class DnsZoneModelEditView(generic.ObjectEditView):
    """Edit view."""

    model = models.DnsZoneModel
    queryset = models.DnsZoneModel.objects.all()
    model_form = forms.DnsZoneModelForm


class DnsZoneModelBulkDeleteView(generic.BulkDeleteView):
    """View for deleting one or more DnsZoneModel records."""

    queryset = models.DnsZoneModel.objects.all()
    table = tables.DnsZoneModelTable


class DnsZoneModelBulkEditView(generic.BulkEditView):
    """View for editing one or more DnsZoneModel records."""

    queryset = models.DnsZoneModel.objects.all()
    table = tables.DnsZoneModelTable
    form = forms.DnsZoneModelBulkEditForm
