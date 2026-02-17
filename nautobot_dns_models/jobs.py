"""Jobs for the DNS app.

This module contains jobs that can be run to manage domain tracking functionality.

Jobs:
    AutoRenewDomains: Job to automatically renew domains that are set to auto-renew

"""

from dateutil.relativedelta import relativedelta
from django.utils import timezone
from nautobot.apps.jobs import Job, register_jobs

from nautobot_dns_models.models import DNSZone

name = "DNS"


class AutoRenewDomains(Job):
    """_Auto Renew Domains."""

    class Meta:
        """Meta attributes."""

        name = "Auto Renew Domains"
        description = (
            "Automatically change expiration date on domains that are set to auto renew on or before today's date."
        )

    def run(self):
        """Run the job."""
        for domain in DNSZone.objects.filter(auto_renewal=True, expiration_date__lte=timezone.now()):
            period = int(domain.renewal_term_months)
            new_date = domain.expiration_date + relativedelta(months=+period)
            self.logger.info(
                "Auto renewing domain %s to %s, auto renewal period is %s months",
                domain.name,
                new_date,
                period,
            )
            domain.expiration_date = new_date
            domain.save()


register_jobs(AutoRenewDomains)
