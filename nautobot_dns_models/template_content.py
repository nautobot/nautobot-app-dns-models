"""Extensions of baseline Nautobot views."""

from constance import config as constance_config
from nautobot.apps.ui import ObjectsTablePanel, SectionChoices, TemplateExtension
from nautobot.core.views.utils import get_obj_from_context
from netutils.ip import ipaddress_address

from nautobot_dns_models.models import AAAARecordModel, ARecordModel, PTRRecordModel
from nautobot_dns_models.tables import (
    AAAARecordModelTable,
    ARecordModelTable,
    PTRRecordModelTable,
)


class ForwardDNSRecordsTablePanel(ObjectsTablePanel):
    """Add A/AAAA DNS Records to the right side of the IP Address page."""

    def should_render(self, context):
        """Check if the table should be rendered."""
        show_panel = constance_config.nautobot_dns_models__IPADDRESS_PANELS["forward"]
        if show_panel == "never":
            return False
        if show_panel == "if_present":
            ip_address = get_obj_from_context(context)
            if ip_address.ip_version == 4:
                return ARecordModel.objects.filter(address=ip_address).exists()
            if ip_address.ip_version == 6:
                return AAAARecordModel.objects.filter(address=ip_address).exists()
        return True

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

    def should_render(self, context):
        """Check if the table should be rendered."""
        show_panel = constance_config.nautobot_dns_models__IPADDRESS_PANELS["reverse"]
        if show_panel == "never":
            return False
        if show_panel == "if_present":
            ip_address = get_obj_from_context(context)
            ptrdname = ipaddress_address(ip_address.host, "reverse_pointer")
            return PTRRecordModel.objects.filter(ptrdname=ptrdname).exists()
        return True

    def get_extra_context(self, context):
        """Set the table class based on the IP version of the IP address."""
        # Calculate the ptrdname based on the IP address.
        ip_address = get_obj_from_context(context)
        ptrdname = ipaddress_address(ip_address.host, "reverse_pointer")

        # Construct the table with the filtered PTR records, apply permissions.
        queryset = PTRRecordModel.objects.filter(ptrdname=ptrdname)
        queryset = queryset.restrict(context.get("request").user, "view")
        ptrdtable = PTRRecordModelTable(queryset)

        # Inject the table into the context.
        context["ptrdtable"] = ptrdtable
        self.context_table_key = "ptrdtable"

        return super().get_extra_context(context)


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
