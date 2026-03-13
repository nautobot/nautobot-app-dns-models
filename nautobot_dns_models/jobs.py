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

name = "DNS"  # pylint: disable=invalid-name


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
        expired_status, created = Status.objects.get_or_create(name="Expired", defaults={"color": "9e9e9e"})
        if created:
            self.logger.info("Created status 'Expired'.")

        if not expired_status.content_types.filter(pk=registration_content_type.pk).exists():
            expired_status.content_types.add(registration_content_type)
            self.logger.info("Associated status 'Expired' with DNS Registration content type.")

        return expired_status

    def run(self, *args, **kwargs):
        """Run the job."""
        update_status_on_expiry = kwargs.get("update_status_on_expiry", False)
        today = timezone.now().date()

        for registration in DNSRegistration.objects.filter(auto_renewal=True, expiration_date__lte=today):
            if registration.renewal_term_months is None:
                self.logger.warning(
                    "Skipping auto renewal for %s: renewal term is not set on registration.",
                    registration.dns_zone,
                )
                continue

            period = int(registration.renewal_term_months)
            self.logger.info("Auto renewal period for %s is %s months", registration.dns_zone, period)
            new_date = registration.expiration_date + relativedelta(months=+period)
            self.logger.info("Auto renewing %s to %s", registration.dns_zone, new_date)
            registration.expiration_date = new_date
            registration.validated_save()

        if not update_status_on_expiry:
            return

        expired_status = self._get_or_create_expired_status()

        expired_registrations = DNSRegistration.objects.filter(auto_renewal=False, expiration_date__lte=today).exclude(
            status=expired_status
        )
        for registration in expired_registrations:
            self.logger.info("Setting registration for %s to Expired", registration.dns_zone)
            registration.status = expired_status
            registration.validated_save()


register_jobs(AutoRenewDomains)
