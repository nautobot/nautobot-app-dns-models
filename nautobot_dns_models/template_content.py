"""Extensions of baseline Nautobot views."""

from urllib.parse import urlencode

from constance import config as constance_config
from django.urls import reverse
from nautobot.apps.ui import ObjectsTablePanel, SectionChoices, TemplateExtension
from nautobot.core.views.utils import get_obj_from_context
from netutils.ip import ipaddress_address

from nautobot_dns_models.models import (
    AAAARecord,
    ARecord,
    DNSZone,
    PTRRecord,
)
from nautobot_dns_models.tables import (
    AAAARecordTable,
    ARecordTable,
    PTRRecordTable,
)


class ForwardDNSRecordsTablePanel(ObjectsTablePanel):
    """Add A/AAAA DNS Records to the right side of the IP Address page."""

    def should_render(self, context):
        """Check if the table should be rendered."""
        show_panel = constance_config.nautobot_dns_models__SHOW_FORWARD_PANEL
        if show_panel == "never":
            return False
        if show_panel == "if_present":
            ip_address = get_obj_from_context(context)
            if ip_address.ip_version == 4:
                return ARecord.objects.filter(ip_address=ip_address).exists()
            if ip_address.ip_version == 6:
                return AAAARecord.objects.filter(ip_address=ip_address).exists()
        return True

    def get_extra_context(self, context):
        """Set the table class based on the IP version of the IP address."""
        # Get the IP address from the context.
        ip_address = get_obj_from_context(context)

        # Use ARecordTable for IPv4 and AAAARecordTable for IPv6.
        url = ""
        if ip_address.ip_version == 4:
            self.table_class = ARecordTable
            url = reverse("plugins:nautobot_dns_models:arecord_add")
        elif ip_address.ip_version == 6:
            self.table_class = AAAARecordTable
            url = reverse("plugins:nautobot_dns_models:aaaarecord_add")

        # Construct the URL query to auto-populate fields when adding a new record.
        autopop_fields = {"ip_address": ip_address.id}
        try:
            name, zone = ip_address.dns_name.split(".", 1)
        except ValueError:
            name = zone = ""
        if DNSZone.objects.filter(name=zone).exists():
            autopop_fields["name"] = name
            autopop_fields["zone"] = DNSZone.objects.get(name=zone).id

        # Tweak returned ctx
        ctx = super().get_extra_context(context)
        return_url = reverse("ipam:ipaddress", kwargs={"pk": ip_address.pk})
        ctx["body_content_table_add_url"] = f"{url}?{urlencode(autopop_fields)}&return_url={return_url}"
        return ctx


class ReverseDNSRecordsTablePanel(ObjectsTablePanel):
    """Add PTR DNS Records to the right side of the IP Address page."""

    def should_render(self, context):
        """Check if the table should be rendered."""
        show_panel = constance_config.nautobot_dns_models__SHOW_REVERSE_PANEL
        if show_panel == "never":
            return False
        if show_panel == "if_present":
            ip_address = get_obj_from_context(context)
            ptrdname = ipaddress_address(ip_address.host, "reverse_pointer")
            return PTRRecord.objects.filter(ptrdname=ptrdname).exists()
        return True

    def get_extra_context(self, context):
        """Set the table class based on the IP version of the IP address."""
        # Calculate the ptrdname based on the IP address.
        ip_address = get_obj_from_context(context)
        ptrdname = ipaddress_address(ip_address.host, "reverse_pointer")

        # Construct the table with the filtered PTR records, apply permissions.
        queryset = PTRRecord.objects.filter(ptrdname=ptrdname)
        queryset = queryset.restrict(context.get("request").user, "view")
        ptrdtable = PTRRecordTable(queryset)

        # Inject the table into the context.
        context["ptrdtable"] = ptrdtable
        self.context_table_key = "ptrdtable"

        # Construct the URL query to auto-populate fields when adding a new record.
        autopop_fields = {
            "ip_address": ip_address.id,
            "name": ip_address.dns_name,
            "ptrdname": ptrdname,
        }
        try:
            zone = ptrdname.split(".", 1)[1]
        except ValueError:
            zone = ""
        if DNSZone.objects.filter(name=zone).exists():
            autopop_fields["zone"] = DNSZone.objects.get(name=zone).id

        # Tweak returned ctx
        url = reverse("plugins:nautobot_dns_models:ptrrecord_add")
        return_url = reverse("ipam:ipaddress", kwargs={"pk": ip_address.pk})
        ctx = super().get_extra_context(context)
        ctx["body_content_table_add_url"] = f"{url}?{urlencode(autopop_fields)}&return_url={return_url}"
        return ctx


class IPAddressDNSRecords(TemplateExtension):  # pylint: disable=abstract-method
    """Add DNS Records to the right side of the IP Address page."""

    model = "ipam.ipaddress"

    object_detail_panels = [
        ForwardDNSRecordsTablePanel(
            weight=100,
            section=SectionChoices.RIGHT_HALF,
            table_class=ARecordTable,
            table_filter="ip_address",
            include_columns=["name", "zone", "ttl", "actions"],
        ),
        ReverseDNSRecordsTablePanel(
            weight=110,
            section=SectionChoices.RIGHT_HALF,
            table_class=PTRRecordTable,
            table_filter="ptrdname",
            include_columns=["name", "zone", "ttl", "actions"],
        ),
    ]


template_extensions = [IPAddressDNSRecords]
