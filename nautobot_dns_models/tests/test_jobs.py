"""Tests for DNS jobs."""

from datetime import timedelta
from unittest import skipIf

from django.contrib.contenttypes.models import ContentType
from django.db import connection
from django.utils import timezone
from nautobot.apps.testing import TestCase
from nautobot.extras.models import Status

from nautobot_dns_models.jobs import AutoRenewDomains, CheckDNSZoneNameCollisions
from nautobot_dns_models.models import DNSRegistrar, DNSRegistration, DNSView, DNSZone


class TestAutoRenewDomainsJob(TestCase):
    """Tests for AutoRenewDomains job behavior."""

    @classmethod
    def setUpTestData(cls):
        """Create shared status objects for tests."""
        super().setUpTestData()
        cls.active_status = Status.objects.get(name="Active")
        cls.expired_status, _ = Status.objects.get_or_create(name="Expired", defaults={"color": "9e9e9e"})
        registration_content_type = ContentType.objects.get_for_model(DNSRegistration)
        cls.active_status.content_types.add(registration_content_type)
        cls.expired_status.content_types.add(registration_content_type)

        cls.view = DNSView.objects.create(name="Job Test View")
        cls.registrar = DNSRegistrar.objects.create(name="Job Test Registrar")
        cls.zone = DNSZone.objects.create(
            name="job-test.example.com",
            dns_view=cls.view,
            ttl=3600,
            filename="job-test.example.com.db",
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
        registration = DNSRegistration.objects.create(
            dns_registrar=self.registrar,
            dns_zone=self.zone,
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
        registration = DNSRegistration.objects.create(
            dns_registrar=self.registrar,
            dns_zone=self.zone,
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
        previous_date = timezone.now().date() - timedelta(days=1)
        registration = DNSRegistration.objects.create(
            dns_registrar=self.registrar,
            dns_zone=self.zone,
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

        registration = DNSRegistration.objects.create(
            dns_registrar=self.registrar,
            dns_zone=self.zone,
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


class TestCheckDNSZoneNameCollisionsJob(TestCase):
    """Tests for CheckDNSZoneNameCollisions job behavior."""

    @classmethod
    def setUpTestData(cls):
        """Create a zone and two views for collision tests."""
        super().setUpTestData()
        cls.view = DNSView.objects.create(name="Collision View")
        cls.other_view = DNSView.objects.create(name="Other Collision View")
        cls.zone = DNSZone.objects.create(name="Example.com", dns_view=cls.view)

    def test_same_name_in_different_views_is_not_a_collision(self):
        """Check same name in different views doesn't cause an issue."""
        DNSZone.objects.create(name="Example.com", dns_view=self.other_view)

        job = CheckDNSZoneNameCollisions()
        with self.assertLogs(job.logger, level="INFO") as logs:
            job.run()

        self.assertEqual(len(logs.records), 1)
        self.assertEqual(logs.records[0].levelname, "INFO")
        self.assertIn("No DNS zone name collisions found.", logs.output[0])

    @skipIf(connection.vendor == "mysql", "MySQL rejects case only duplicates with built-in mechanism.")
    def test_case_only_collision_in_same_view_logs_warning(self):
        """Check that collisions produce warning logs."""
        DNSZone.objects.create(name="example.com", dns_view=self.view)

        job = CheckDNSZoneNameCollisions()
        with self.assertLogs(job.logger, level="INFO") as logs:
            job.run()

        self.assertTrue(all(record.levelname == "WARNING" for record in logs.records))
        self.assertIn('View "Collision View"', logs.output[0])
        self.assertIn('"Example.com" (0 record(s))', logs.output[0])
        self.assertIn('"example.com" (0 record(s))', logs.output[0])
        self.assertIn("Rename, merge, or delete the colliding zones before upgrading.", logs.output[-1])
