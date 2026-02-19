"""Jobs for the DNS app.

This module contains jobs that can be run to manage domain tracking functionality.

Jobs:
    AutoRenewDomains: Job to automatically renew domains that are set to auto-renew

"""

from dateutil.relativedelta import relativedelta
from django.contrib.contenttypes.models import ContentType
from django.utils import timezone
from nautobot.apps.jobs import BooleanVar, Job, register_jobs
from nautobot.extras.models import Status

from nautobot_dns_models.models import DNSRegistration

name = "DNS"


class AutoRenewDomains(Job):
    """_Auto Renew Domains."""

    update_status_on_expiry = BooleanVar(
        required=False,
        default=False,
        label="Set status to Expired when expired and auto renewal is disabled",
    )

    class Meta:
        """Meta attributes."""

        name = "Auto Renew Domains"
        description = (
            "Automatically change expiration date on domains that are set to auto renew on or before today's date."
        )

    def _get_or_create_expired_status(self):
        """Get or create Expired status and ensure it supports DNSRegistration."""
        registration_content_type = ContentType.objects.get_for_model(DNSRegistration)

        expired_status = Status.objects.filter(name="Expired", content_types=registration_content_type).first()
        if expired_status is not None:
            return expired_status

        expired_status = Status.objects.filter(name="Expired").first()
        if expired_status is None:
            expired_status = Status.objects.create(name="Expired", color="9e9e9e")
            self.logger.info("Created status 'Expired'.")

        if not expired_status.content_types.filter(pk=registration_content_type.pk).exists():
            expired_status.content_types.add(registration_content_type)
            self.logger.info("Associated status 'Expired' with DNS Registration content type.")

        return expired_status

    def run(self, update_status_on_expiry=False):
        """Run the job."""
        today = timezone.now().date()

        for registration in DNSRegistration.objects.filter(auto_renewal=True, expiration_date__lte=today):
            if registration.renewal_term_months is None:
                self.logger.warning(
                    f"Skipping auto renewal for {registration.dns_zone}: renewal term is not set on registration."
                )
                continue

            period = int(registration.renewal_term_months)
            self.logger.info(f"Auto renewal period for {registration.dns_zone} is {period} months")
            new_date = registration.expiration_date + relativedelta(months=+period)
            self.logger.info(f"Auto renewing {registration.dns_zone} to {new_date}")
            registration.expiration_date = new_date
            registration.save()

        if not update_status_on_expiry:
            return

        expired_status = self._get_or_create_expired_status()

        expired_registrations = DNSRegistration.objects.filter(auto_renewal=False, expiration_date__lte=today).exclude(
            status=expired_status
        )
        for registration in expired_registrations:
            self.logger.info(f"Setting registration for {registration.dns_zone} to Expired")
            registration.status = expired_status
            registration.save()


register_jobs(AutoRenewDomains)
