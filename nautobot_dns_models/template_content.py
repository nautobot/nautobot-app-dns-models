"""Extensions of baseline Nautobot views."""

from nautobot.apps.ui import TemplateExtension

from .models import AAAARecordModel, ARecordModel


class IPAddressDNSRecords(TemplateExtension):  # pylint: disable=abstract-method
    """Add DNS A Records to the right side of the IP Address page."""

    model = "ipam.ipaddress"

    def right_page(self):
        """Add content to the right side of the IP Address page."""
        dns_records = None
        dns_records_type = None

        # Check if the IP address is IPv4 or IPv6
        ip_version = self.context["object"].ip_version
        if ip_version == 4:
            dns_records = ARecordModel.objects.filter(
                address=self.context["object"],
            )
            dns_records_type = "A"
        elif ip_version == 6:
            dns_records = AAAARecordModel.objects.filter(
                address=self.context["object"],
            )
            dns_records_type = "AAAA"
        return self.render(
            "nautobot_dns_models/inc/ipaddress_dns_records.html",
            extra_context={
                "dns_records": dns_records,
                "dns_records_type": dns_records_type,
            },
        )


template_extensions = [IPAddressDNSRecords]
