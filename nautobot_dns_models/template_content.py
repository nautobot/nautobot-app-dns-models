"""Extensions of baseline Nautobot views."""

from nautobot.apps.ui import ObjectsTablePanel, SectionChoices, TemplateExtension
from nautobot.core.views.utils import get_obj_from_context
from netutils.ip import ipaddress_address

from nautobot_dns_models.models import PTRRecordModel
from nautobot_dns_models.tables import (
    AAAARecordModelTable,
    ARecordModelTable,
    PTRRecordModelTable,
)


class ForwardDNSRecordsTablePanel(ObjectsTablePanel):
    """Add A/AAAA DNS Records to the right side of the IP Address page."""

    def get_extra_context(self, context):
        """Set the table class based on the IP version of the IP address."""
        # Get the IP address from the context.
        ip_address = get_obj_from_context(context)

        # Use ARecordModelTable for IPv4 and AAAARecordModelTable for IPv6.
        if ip_address.ip_version == 4:
            self.table_class = ARecordModelTable
        elif ip_address.ip_version == 6:
            self.table_class = AAAARecordModelTable

        return super().get_extra_context(context)


class ReverseDNSRecordsTablePanel(ObjectsTablePanel):
    """Add PTR DNS Records to the right side of the IP Address page."""

    def get_extra_context(self, context):
        """Set the table class based on the IP version of the IP address."""
        user = context.get("request").user
        if user.has_perm("nautobot_dns_models.view_ptrrecordmodel"):
            # Calculate the `ptrdname`` based on the IP address.
            ip_address = get_obj_from_context(context)
            ptrdname = ipaddress_address(ip_address.host, "reverse_pointer")

            # Construct the table with the filtered PTR records.
            queryset = PTRRecordModel.objects.filter(ptrdname=ptrdname)
            ptrdtable = PTRRecordModelTable(queryset)

            # Inject the table into the context.
            context["ptrdtable"] = ptrdtable
            self.context_table_key = "ptrdtable"

        return super().get_extra_context(context)


# This class is named IPAddressDNSRecords (instead of e.g. IPAddressARecords) as
# eventually it will also host the PTR records too.
class IPAddressDNSRecords(TemplateExtension):  # pylint: disable=abstract-method
    """Add DNS Records to the right side of the IP Address page."""

    model = "ipam.ipaddress"

    object_detail_panels = [
        ForwardDNSRecordsTablePanel(
            weight=100,
            section=SectionChoices.RIGHT_HALF,
            table_class=ARecordModelTable,
            table_filter="address",
            include_columns=["name", "zone", "ttl", "actions"],
        ),
        ReverseDNSRecordsTablePanel(
            weight=100,
            section=SectionChoices.RIGHT_HALF,
            table_class=PTRRecordModelTable,
            table_filter="ptrdname",
            include_columns=["name", "zone", "ttl", "actions"],
        ),
    ]


template_extensions = [IPAddressDNSRecords]
