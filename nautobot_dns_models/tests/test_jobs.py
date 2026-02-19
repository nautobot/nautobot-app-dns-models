"""Tests for DNS jobs."""

from datetime import timedelta

from django.contrib.contenttypes.models import ContentType
from django.utils import timezone
from nautobot.apps.testing import TestCase
from nautobot.extras.models import Status

from nautobot_dns_models.jobs import AutoRenewDomains
from nautobot_dns_models.models import DNSRegistrar, DNSRegistration, DNSView, DNSZone


class TestAutoRenewDomainsJob(TestCase):
    """Tests for AutoRenewDomains job behavior."""

    @classmethod
    def setUpTestData(cls):
        """Create shared status objects for tests."""
        super().setUpTestData()
        cls.active_status = Status.objects.get(name="Active")
        cls.expired_status, _ = Status.objects.get_or_create(name="Expired", defaults={"color": "9e9e9e"})
        cls.expired_status.content_types.add(ContentType.objects.get_for_model(DNSRegistration))
        cls.view = DNSView.objects.create(name="Job Test View")
        cls.registrar = DNSRegistrar.objects.create(name="Job Test Registrar")

    def _create_zone(self, name):
        return DNSZone.objects.create(
            name=name,
            dns_view=self.view,
            ttl=3600,
            filename=f"{name}.db",
            soa_mname="ns1.example.com",
            soa_rname="admin@example.com",
            soa_refresh=86400,
            soa_retry=7200,
            soa_expire=3600000,
            soa_serial=1,
            soa_minimum=3600,
        )

    def test_toggle_disabled_does_not_change_status(self):
        """When toggle is disabled, status should not change for expired non-auto-renew registrations."""
        zone = self._create_zone("disabled.example.com")
        registration = DNSRegistration.objects.create(
            dns_registrar=self.registrar,
            dns_zone=zone,
            status=self.active_status,
            expiration_date=timezone.now().date() - timedelta(days=1),
            auto_renewal=False,
        )

        job = AutoRenewDomains()
        job.run(update_status_on_expiry=False)

        registration.refresh_from_db()
        self.assertEqual(registration.status, self.active_status)

    def test_toggle_enabled_marks_non_auto_renewed_registration_expired(self):
        """When toggle is enabled, expired non-auto-renew registrations should be set to Expired."""
        zone = self._create_zone("enable.example.com")
        registration = DNSRegistration.objects.create(
            dns_registrar=self.registrar,
            dns_zone=zone,
            status=self.active_status,
            expiration_date=timezone.now().date() - timedelta(days=1),
            auto_renewal=False,
        )

        job = AutoRenewDomains()
        job.run(update_status_on_expiry=True)

        registration.refresh_from_db()
        self.assertEqual(registration.status, self.expired_status)

    def test_auto_renew_enabled_extends_expiration(self):
        """Expired registrations with auto renewal enabled should have expiration extended."""
        zone = self._create_zone("renew.example.com")
        previous_date = timezone.now().date() - timedelta(days=1)
        registration = DNSRegistration.objects.create(
            dns_registrar=self.registrar,
            dns_zone=zone,
            status=self.active_status,
            expiration_date=previous_date,
            auto_renewal=True,
            renewal_term_months=12,
        )

        job = AutoRenewDomains()
        job.run(update_status_on_expiry=True)

        registration.refresh_from_db()
        self.assertGreater(registration.expiration_date, previous_date)
        self.assertEqual(registration.status, self.active_status)

    def test_toggle_enabled_creates_and_associates_expired_status_when_missing(self):
        """Toggle should create Expired status and associate DNSRegistration content type when needed."""
        registration_content_type = ContentType.objects.get_for_model(DNSRegistration)

        Status.objects.filter(name="Expired").delete()

        zone = self._create_zone("create-expired.example.com")
        registration = DNSRegistration.objects.create(
            dns_registrar=self.registrar,
            dns_zone=zone,
            status=self.active_status,
            expiration_date=timezone.now().date() - timedelta(days=1),
            auto_renewal=False,
        )

        job = AutoRenewDomains()
        job.run(update_status_on_expiry=True)

        expired_status = Status.objects.filter(name="Expired", content_types=registration_content_type).first()
        self.assertIsNotNone(expired_status)

        registration.refresh_from_db()
        self.assertEqual(registration.status, expired_status)
