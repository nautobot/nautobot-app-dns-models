"""Extensions of baseline Nautobot views."""

from nautobot.apps.ui import ObjectsTablePanel, SectionChoices, TemplateExtension
from nautobot.core.views.utils import get_obj_from_context
from netutils.ip import ipaddress_address

from nautobot_dns_models.models import PTRRecordModel
from nautobot_dns_models.tables import AAAARecordModelTable, ARecordModelTable


class ForwardDNSRecordsTablePanel(ObjectsTablePanel):
    """Add A/AAAA DNS Records to the right side of the IP Address page."""

    def get_extra_context(self, context):
        """Set the table class based on the IP version of the IP address."""
        # ip_version = context.dicts[3]["object"].ip_version
        ip_address = get_obj_from_context(context)
        if ip_address.ip_version == 4:
            self.table_class = ARecordModelTable
        elif ip_address.ip_version == 6:
            self.table_class = AAAARecordModelTable
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
            # table_class is dynamically set in ForwardDNSRecordsTablePanel.get_extra_context
            table_filter="address",
            include_columns=["name", "zone", "ttl", "actions"],
        )
    ]


# TODO: Discuss whether PTR Records must have an FK to IP Address (like A/AAAA).
# If yes, change this to use the UI Component Framework (add to the above class).
class IPAddressPTRRecords(TemplateExtension):  # pylint: disable=abstract-method
    """Add DNS PTR Records to the right side of the IP Address page."""

    model = "ipam.ipaddress"

    def right_page(self):
        """Add content to the right side of the IP Address page."""
        ptrdname = ipaddress_address(self.context["object"].host, "reverse_pointer")
        return self.render(
            "nautobot_dns_models/inc/ipaddress_ptr_records.html",
            extra_context={
                "ptr_records": PTRRecordModel.objects.filter(ptrdname=ptrdname),
                "ptrdname": ptrdname,
            },
        )


template_extensions = [IPAddressDNSRecords, IPAddressPTRRecords]
