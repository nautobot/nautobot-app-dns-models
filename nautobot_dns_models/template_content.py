"""Extensions of baseline Nautobot views."""

from nautobot.apps.ui import TemplateExtension
from netutils.ip import ipaddress_address

from .models import AAAARecordModel, ARecordModel, PTRRecordModel


class IPAddressARecords(TemplateExtension):  # pylint: disable=abstract-method
    """Add DNS A Records to the right side of the IP Address page."""

    model = "ipam.ipaddress"

    def right_page(self):
        """Add content to the right side of the IP Address page."""
        ip_version = self.context["object"].ip_version
        user = self.context["request"].user
        if (ip_version == 4) and (user.has_perm("nautobot_dns_models.view_arecordmodel")):
            return self.render(
                "nautobot_dns_models/inc/ipaddress_dns_records.html",
                extra_context={
                    "dns_records": ARecordModel.objects.filter(address=self.context["object"]),
                    "dns_records_type": "A",
                },
            )
        return ""


class IPAddressAAAARecords(TemplateExtension):  # pylint: disable=abstract-method
    """Add DNS AAAA Records to the right side of the IP Address page."""

    model = "ipam.ipaddress"

    def right_page(self):
        """Add content to the right side of the IP Address page."""
        ip_version = self.context["object"].ip_version
        user = self.context["request"].user
        if (ip_version == 6) and (user.has_perm("nautobot_dns_models.view_aaaarecordmodel")):
            return self.render(
                "nautobot_dns_models/inc/ipaddress_dns_records.html",
                extra_context={
                    "dns_records": AAAARecordModel.objects.filter(address=self.context["object"]),
                    "dns_records_type": "AAAA",
                },
            )
        return ""


class IPAddressPTRRecords(TemplateExtension):  # pylint: disable=abstract-method
    """Add DNS PTR Records to the right side of the IP Address page."""

    model = "ipam.ipaddress"

    def right_page(self):
        """Add content to the right side of the IP Address page."""
        ptrdname = ipaddress_address(self.context["object"].host, "reverse_pointer")
        user = self.context["request"].user
        if user.has_perm("nautobot_dns_models.view_ptrrecordmodel"):
            return self.render(
                "nautobot_dns_models/inc/ipaddress_dns_records.html",
                extra_context={
                    "dns_records": PTRRecordModel.objects.filter(ptrdname=ptrdname),
                    "dns_records_type": "PTR",
                    "ptrdname": ptrdname,
                },
            )
        return ""


template_extensions = [IPAddressARecords, IPAddressAAAARecords, IPAddressPTRRecords]
