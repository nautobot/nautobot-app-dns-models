"""Unit tests for nautobot_dns_models."""

from datetime import date

from constance.test import override_config
from django.contrib.contenttypes.models import ContentType
from django.test import override_settings
from django.urls import reverse
from nautobot.apps.api import get_serializer_for_model
from nautobot.apps.testing import APIViewTestCases
from nautobot.core.testing import utils
from nautobot.extras.models.statuses import Status
from nautobot.ipam.models import IPAddress, Namespace, Prefix
from rest_framework import status
from rest_framework.relations import ManyRelatedField

from nautobot_dns_models.models import (
    AAAARecord,
    ARecord,
    CNAMERecord,
    DNSRegistrar,
    DNSRegistration,
    DNSView,
    DNSViewPrefixAssignment,
    DNSZone,
    MXRecord,
    NSRecord,
    PTRRecord,
    SRVRecord,
    TXTRecord,
)


def _create_zone(name, dns_view=None):
    return DNSZone.objects.create(
        name=name,
        dns_view=dns_view,
        filename=f"{name}.zone",
        soa_mname=f"ns1.{name}",
        soa_rname=f"admin@{name}",
    )


class DNSViewAPITestCase(APIViewTestCases.APIViewTestCase):
    """Test the Nautobot DNSView API."""

    model = DNSView
    view_namespace = "plugins-api:nautobot_dns_models"
    bulk_update_data = {
        "description": "Example bulk description",
    }
    brief_fields = [
        "name",
    ]

    @classmethod
    def setUpTestData(cls):
        DNSView.objects.create(name="View 1", description="First DNS View")
        DNSView.objects.create(name="View 2", description="Second DNS View")
        DNSView.objects.create(name="View 3", description="Third DNS View")

        cls.create_data = [
            {
                "name": "View 4",
                "description": "Fourth DNS View",
            },
            {
                "name": "View 5",
                "description": "Fifth DNS View",
            },
            {
                "name": "View 6",
                "description": "Sixth DNS View",
            },
        ]


class DNSViewPrefixAssignmentAPITestCase(APIViewTestCases.APIViewTestCase):
    """Test the Nautobot DNSViewPrefixAssignment API."""

    model = DNSViewPrefixAssignment
    view_namespace = "plugins-api:nautobot_dns_models"

    brief_fields = [
        "dns_view",
        "prefix",
    ]

    @classmethod
    def setUpTestData(cls):
        namespace = Namespace.objects.get(name="Global")
        active_status = Status.objects.get(name="Active")
        prefixes = (
            Prefix.objects.create(prefix="192.0.2.0/24", namespace=namespace, status=active_status),
            Prefix.objects.create(prefix="192.0.2.0/25", namespace=namespace, status=active_status),
            Prefix.objects.create(prefix="192.0.3.0/24", namespace=namespace, status=active_status),
        )

        dns_views = (
            DNSView.objects.create(name="View 1", description="First DNS View"),
            DNSView.objects.create(name="View 2", description="Second DNS View"),
            DNSView.objects.create(name="View 3", description="Third DNS View"),
        )

        DNSViewPrefixAssignment.objects.create(dns_view=dns_views[0], prefix=prefixes[0])
        DNSViewPrefixAssignment.objects.create(dns_view=dns_views[0], prefix=prefixes[1])
        DNSViewPrefixAssignment.objects.create(dns_view=dns_views[2], prefix=prefixes[1])

        cls.create_data = [
            {
                "dns_view": dns_views[1].pk,
                "prefix": prefixes[0].pk,
            },
            {
                "dns_view": dns_views[1].pk,
                "prefix": prefixes[2].pk,
            },
        ]


class DNSRegistrarAPITestCase(APIViewTestCases.APIViewTestCase):
    """Test the Nautobot DNSRegistrar API."""

    model = DNSRegistrar
    view_namespace = "plugins-api:nautobot_dns_models"
    bulk_update_data = {
        "account_number": "UPDATED-ACCOUNT",
    }
    brief_fields = [
        "name",
        "url",
        "account_number",
    ]

    @classmethod
    def setUpTestData(cls):
        DNSRegistrar.objects.create(name="Registrar 1", url="https://registrar1.example", account_number="ACC-001")
        DNSRegistrar.objects.create(name="Registrar 2", url="https://registrar2.example", account_number="ACC-002")
        DNSRegistrar.objects.create(name="Registrar 3", url="https://registrar3.example", account_number="ACC-003")

        cls.create_data = [
            {
                "name": "Registrar 4",
                "url": "https://registrar4.example",
                "account_number": "ACC-004",
            },
            {
                "name": "Registrar 5",
                "url": "https://registrar5.example",
                "account_number": "ACC-005",
            },
            {
                "name": "Registrar 6",
                "url": "https://registrar6.example",
                "account_number": "ACC-006",
            },
        ]

    @override_settings(EXEMPT_VIEW_PERMISSIONS=["*"])
    def test_recreate_object_csv(self):
        """CSV recreate test excluding model `url`, which Nautobot omits from CSV headers."""
        instance = utils.get_deletable_objects(self.model, self._get_queryset()).first()
        if instance is None:
            self.fail("Couldn't find a single deletable object!")

        self.add_permissions(
            f"{self.model._meta.app_label}.add_{self.model._meta.model_name}",
            f"{self.model._meta.app_label}.view_{self.model._meta.model_name}",
        )

        response = self.client.get(self._get_detail_url(instance) + "?format=csv", **self.header)
        self.assertHttpStatus(response, status.HTTP_200_OK)
        csv_data = response.content.decode(response.charset)

        serializer_class = get_serializer_for_model(self.model)
        old_data = serializer_class(instance, context={"request": None}).data
        orig_pk = instance.pk
        instance.delete()

        response = self.client.post(self._get_list_url(), csv_data, content_type="text/csv", **self.header)
        self.assertHttpStatus(response, status.HTTP_201_CREATED, csv_data)
        new_instance = self._get_queryset().get(pk=response.data[0]["id"])
        if isinstance(orig_pk, int):
            self.assertNotEqual(new_instance.pk, orig_pk)
        else:
            self.assertEqual(new_instance.pk, orig_pk)

        new_serializer = serializer_class(new_instance, context={"request": None})
        new_data = new_serializer.data
        for field_name, field in new_serializer.fields.items():
            if isinstance(field, ManyRelatedField) and field_name != "tags":
                continue
            if field.read_only or field.write_only or field_name == "url":
                continue
            if field_name in ["created", "last_updated"]:
                self.assertNotEqual(old_data[field_name], new_data[field_name])
            else:
                self.assertEqual(old_data[field_name], new_data[field_name])

    def test_post_dnsregistrar_fails_invalid_url(self):
        """Attempting to create a registrar with invalid URL should fail."""
        self.add_permissions("nautobot_dns_models.add_dnsregistrar")

        url = reverse("plugins-api:nautobot_dns_models-api:dnsregistrar-list")
        data = {
            "name": "Bad URL Registrar",
            "url": "not-a-valid-url",
            "account_number": "ACC-BAD-URL",
        }

        response = self.client.post(url, data=data, format="json", **self.header)
        self.assertHttpStatus(response, status.HTTP_400_BAD_REQUEST)

    def test_post_dnsregistrar_fails_duplicate_name(self):
        """Attempting to create a registrar with a duplicate name should fail."""
        self.add_permissions("nautobot_dns_models.add_dnsregistrar")

        url = reverse("plugins-api:nautobot_dns_models-api:dnsregistrar-list")
        data = {
            "name": "Registrar 1",
            "url": "https://duplicate-registrar.example",
            "account_number": "ACC-DUPLICATE",
        }

        response = self.client.post(url, data=data, format="json", **self.header)
        self.assertHttpStatus(response, status.HTTP_400_BAD_REQUEST)


class DNSRegistrationAPITestCase(APIViewTestCases.APIViewTestCase):
    """Test the Nautobot DNSRegistration API."""

    model = DNSRegistration
    view_namespace = "plugins-api:nautobot_dns_models"
    bulk_update_data = {
        "auto_renewal": True,
        "renewal_term_months": 24,
    }
    brief_fields = [
        "dns_registrar",
        "dns_zone",
        "status",
    ]

    @classmethod
    def setUpTestData(cls):
        registration_ct = ContentType.objects.get_for_model(DNSRegistration)
        cls.active_status = Status.objects.get(name="Active")
        cls.active_status.content_types.add(registration_ct)
        cls.pending_status, _ = Status.objects.get_or_create(name="Pending Registration", defaults={"color": "ff9800"})
        cls.pending_status.content_types.add(registration_ct)

        cls.dns_view = DNSView.objects.create(
            name="Registration API View", description="View for registration API tests"
        )
        cls.dns_registrars = (
            DNSRegistrar.objects.create(
                name="Reg API Registrar 1", url="https://reg-api-1.example", account_number="R1"
            ),
            DNSRegistrar.objects.create(
                name="Reg API Registrar 2", url="https://reg-api-2.example", account_number="R2"
            ),
            DNSRegistrar.objects.create(
                name="Reg API Registrar 3", url="https://reg-api-3.example", account_number="R3"
            ),
        )
        cls.dns_zones = tuple(
            _create_zone(name=name, dns_view=cls.dns_view)
            for name in ("reg-api-one.example", "reg-api-two.example", "reg-api-three.example")
        )

        DNSRegistration.objects.create(
            dns_registrar=cls.dns_registrars[0],
            dns_zone=cls.dns_zones[0],
            status=cls.active_status,
            expiration_date=date(2026, 1, 15),
            auto_renewal=False,
            renewal_term_months=12,
        )
        DNSRegistration.objects.create(
            dns_registrar=cls.dns_registrars[1],
            dns_zone=cls.dns_zones[1],
            status=cls.pending_status,
            expiration_date=date(2026, 6, 1),
            auto_renewal=True,
            dnssec_enabled=True,
            renewal_term_months=24,
        )
        DNSRegistration.objects.create(
            dns_registrar=cls.dns_registrars[2],
            dns_zone=cls.dns_zones[2],
            status=cls.active_status,
            expiration_date=date(2027, 1, 10),
            auto_renewal=False,
            renewal_term_months=36,
        )

        cls.create_data = [
            {
                "dns_registrar": cls.dns_registrars[0].id,
                "dns_zone": cls.dns_zones[1].id,
                "status": cls.active_status.id,
                "expiration_date": date(2027, 2, 1),
                "auto_renewal": True,
                "renewal_term_months": 12,
            },
            {
                "dns_registrar": cls.dns_registrars[1].id,
                "dns_zone": cls.dns_zones[2].id,
                "status": cls.pending_status.id,
                "expiration_date": date(2027, 4, 1),
                "registry_locked": True,
                "transfer_locked": True,
                "renewal_term_months": 6,
            },
            {
                "dns_registrar": cls.dns_registrars[2].id,
                "dns_zone": cls.dns_zones[0].id,
                "status": cls.active_status.id,
                "expiration_date": date(2028, 1, 1),
                "privacy_enabled": True,
                "website_forwarding_enabled": False,
                "renewal_term_months": 18,
            },
        ]

    @staticmethod
    def _response_results(response):
        """Return list endpoint results regardless of pagination mode."""
        if isinstance(response.data, list):
            return response.data
        return response.data.get("results", [])

    def test_post_dnsregistration_fails_duplicate_registrar_zone(self):
        """Duplicate (dns_registrar, dns_zone) should be rejected."""
        self.add_permissions("nautobot_dns_models.add_dnsregistration")

        url = reverse("plugins-api:nautobot_dns_models-api:dnsregistration-list")
        data = {
            "dns_registrar": self.dns_registrars[0].id,
            "dns_zone": self.dns_zones[0].id,
            "status": self.active_status.id,
            "expiration_date": "2028-02-15",
        }

        response = self.client.post(url, data=data, format="json", **self.header)
        self.assertHttpStatus(response, status.HTTP_400_BAD_REQUEST)

    def test_post_dnsregistration_fails_invalid_renewal_term_bounds(self):
        """Renewal term outside min/max bounds should be rejected."""
        self.add_permissions("nautobot_dns_models.add_dnsregistration")

        url = reverse("plugins-api:nautobot_dns_models-api:dnsregistration-list")
        for renewal_term in [0, 1201]:
            with self.subTest(renewal_term_months=renewal_term):
                data = {
                    "dns_registrar": self.dns_registrars[0].id,
                    "dns_zone": self.dns_zones[1].id,
                    "status": self.active_status.id,
                    "renewal_term_months": renewal_term,
                }
                response = self.client.post(url, data=data, format="json", **self.header)
                self.assertHttpStatus(response, status.HTTP_400_BAD_REQUEST)

    def test_post_dnsregistration_fails_without_status(self):
        """Status is required when creating a registration."""
        self.add_permissions("nautobot_dns_models.add_dnsregistration")

        url = reverse("plugins-api:nautobot_dns_models-api:dnsregistration-list")
        data = {
            "dns_registrar": self.dns_registrars[1].id,
            "dns_zone": self.dns_zones[0].id,
            "auto_renewal": False,
        }

        response = self.client.post(url, data=data, format="json", **self.header)
        self.assertHttpStatus(response, status.HTTP_400_BAD_REQUEST)

    def test_patch_dnsregistration_toggles_auto_renewal(self):
        """Partial update should allow toggling a boolean field."""
        self.add_permissions("nautobot_dns_models.change_dnsregistration")

        instance = DNSRegistration.objects.filter(auto_renewal=False).first()
        self.assertIsNotNone(instance)

        response = self.client.patch(
            self._get_detail_url(instance),
            data={"auto_renewal": True, "dnssec_enabled": True},
            format="json",
            **self.header,
        )
        self.assertHttpStatus(response, status.HTTP_200_OK)

        instance.refresh_from_db()
        self.assertTrue(instance.auto_renewal)
        self.assertTrue(instance.dnssec_enabled)

    def test_filter_dnsregistration_q(self):
        """Search filter should match registrar, zone, and status names."""
        self.add_permissions("nautobot_dns_models.view_dnsregistration")

        response = self.client.get(self._get_list_url(), data={"q": "Reg API Registrar 2"}, **self.header)
        self.assertHttpStatus(response, status.HTTP_200_OK)
        results = self._response_results(response)
        self.assertEqual(len(results), 1)

        response = self.client.get(self._get_list_url(), data={"q": "reg-api-three.example"}, **self.header)
        self.assertHttpStatus(response, status.HTTP_200_OK)
        results = self._response_results(response)
        self.assertEqual(len(results), 1)

        response = self.client.get(self._get_list_url(), data={"q": "Pending Registration"}, **self.header)
        self.assertHttpStatus(response, status.HTTP_200_OK)
        results = self._response_results(response)
        self.assertEqual(len(results), 1)

    def test_filter_dnsregistration_expiration_lte(self):
        """expiration_date__lte should include only registrations expiring on/before date."""
        self.add_permissions("nautobot_dns_models.view_dnsregistration")

        response = self.client.get(self._get_list_url(), data={"expiration_date__lte": "2026-06-01"}, **self.header)
        self.assertHttpStatus(response, status.HTTP_200_OK)
        results = self._response_results(response)
        self.assertEqual(len(results), 2)

    def test_filter_dnsregistration_expiration_gte(self):
        """expiration_date__gte should include only registrations expiring on/after date."""
        self.add_permissions("nautobot_dns_models.view_dnsregistration")

        response = self.client.get(self._get_list_url(), data={"expiration_date__gte": "2026-06-01"}, **self.header)
        self.assertHttpStatus(response, status.HTTP_200_OK)
        results = self._response_results(response)
        self.assertEqual(len(results), 2)


class DNSZoneAPITestCase(APIViewTestCases.APIViewTestCase):
    """Test the Nautobot DNSZone API."""

    model = DNSZone
    view_namespace = "plugins-api:nautobot_dns_models"
    bulk_update_data = {
        "description": "Example bulk description",
    }
    brief_fields = [
        "filename",
        "soa_mname",
        "soa_rname",
    ]

    @classmethod
    def setUpTestData(cls):
        dns_view = DNSView.objects.get(name="Default")
        _create_zone(name="test.com", dns_view=dns_view)
        _create_zone(name="test.org", dns_view=dns_view)
        _create_zone(name="test.net", dns_view=dns_view)

        cls.create_data = [
            {
                "name": "example.com",
                "dns_view": dns_view.id,
                "filename": "example.com.zone",
                "soa_mname": "ns1.example.com",
                "soa_rname": "admin@example.com",
                "soa_refresh": 3600,
                "soa_retry": 600,
            },
            {
                "name": "example.org",
                "dns_view": dns_view.id,
                "filename": "example.org.zone",
                "soa_mname": "ns1.example.org",
                "soa_rname": "admin@example.org",
            },
            {
                "name": "example.net",
                "dns_view": dns_view.id,
                "filename": "example.net.zone",
                "soa_mname": "ns1.example.net",
                "soa_rname": "admin@example.net",
            },
        ]


class NSRecordAPITestCase(APIViewTestCases.APIViewTestCase):
    """Test the Nautobot NSRecord API."""

    model = NSRecord
    view_namespace = "plugins-api:nautobot_dns_models"
    bulk_update_data = {
        "description": "Example bulk description",
    }
    brief_fields = [
        "name",
        "server",
    ]

    @classmethod
    def setUpTestData(cls):
        dns_zone = _create_zone(name="example.com")

        NSRecord.objects.create(name="ns1", server="ns1.example.com.", zone=dns_zone)
        NSRecord.objects.create(name="ns2", server="ns2.example.com.", zone=dns_zone)
        NSRecord.objects.create(name="ns3", server="ns3.example.com.", zone=dns_zone)

        cls.create_data = [
            {
                "name": "ns4",
                "server": "ns4.example.com.",
                "zone": dns_zone.id,
            },
            {
                "name": "ns5",
                "server": "ns5.example.com.",
                "zone": dns_zone.id,
            },
            {
                "name": "ns6",
                "server": "ns6.example.com.",
                "zone": dns_zone.id,
            },
        ]


class ARecordAPITestCase(APIViewTestCases.APIViewTestCase):
    """Test the Nautobot ARecord API."""

    model = ARecord
    view_namespace = "plugins-api:nautobot_dns_models"
    bulk_update_data = {
        "description": "Example bulk description",
    }
    brief_fields = [
        "name",
        "ip_address",
    ]

    @classmethod
    def setUpTestData(cls):
        dns_zone = _create_zone(name="example.com")

        namespace = Namespace.objects.get(name="Global")
        active_status = Status.objects.get(name="Active")
        Prefix.objects.create(prefix="10.0.0.0/24", namespace=namespace, type="Pool", status=active_status)
        ip_addresses = (
            IPAddress.objects.create(address="10.0.0.1/32", namespace=namespace, status=active_status),
            IPAddress.objects.create(address="10.0.0.2/32", namespace=namespace, status=active_status),
        )

        # IPv6 Test Data
        cls.ipv6_zone = DNSZone.objects.create(name="example_ipv6.com")
        Prefix.objects.create(prefix="2001:db8::/64", namespace=namespace, type="Pool", status=active_status)
        cls.invalid_ipv6 = IPAddress.objects.create(
            address="2001:db8::1/128", namespace=namespace, status=active_status
        )

        ARecord.objects.create(name="example.com", ip_address=ip_addresses[0], zone=dns_zone)
        ARecord.objects.create(name="www.example.com", ip_address=ip_addresses[0], zone=dns_zone)
        ARecord.objects.create(name="site.example.com", ip_address=ip_addresses[0], zone=dns_zone)

        cls.create_data = [
            {
                "name": "example.com",
                "ip_address": ip_addresses[1].id,
                "zone": dns_zone.id,
            },
            {
                "name": "www.example.com",
                "ip_address": ip_addresses[1].id,
                "zone": dns_zone.id,
            },
            {
                "name": "site.example.com",
                "ip_address": ip_addresses[1].id,
                "zone": dns_zone.id,
            },
        ]

    def test_create_arecord_with_invalid_ipv6_fails(self):
        """Attempt to create an ARecord using an IPv6 address should fail."""
        self.add_permissions("nautobot_dns_models.add_arecord")

        url = reverse("plugins-api:nautobot_dns_models-api:arecord-list")
        data = {
            "name": "invalid.example.com",
            "ip_address": str(self.invalid_ipv6.id),
            "zone": str(self.ipv6_zone.id),
            "ttl": 3600,
        }

        response = self.client.post(url, data=data, format="json", **self.header)

        self.assertHttpStatus(response, status.HTTP_400_BAD_REQUEST)


class AAAARecordAPITestCase(APIViewTestCases.APIViewTestCase):
    """Test the Nautobot AAAARecord API."""

    model = AAAARecord
    view_namespace = "plugins-api:nautobot_dns_models"
    bulk_update_data = {
        "description": "Example bulk description",
    }
    brief_fields = [
        "name",
        "ip_address",
    ]

    @classmethod
    def setUpTestData(cls):
        dns_zone = _create_zone(name="example.com")

        active_status = Status.objects.get(name="Active")
        namespace = Namespace.objects.get(name="Global")
        Prefix.objects.create(prefix="2001:db8:abcd:12::/64", namespace=namespace, type="Pool", status=active_status)
        ip_addresses = (
            IPAddress.objects.create(address="2001:db8:abcd:12::1/128", namespace=namespace, status=active_status),
            IPAddress.objects.create(address="2001:db8:abcd:12::2/128", namespace=namespace, status=active_status),
        )

        # IPv4 Test Data
        cls.zone = DNSZone.objects.create(name="example_ipv4.com")
        Prefix.objects.create(prefix="10.0.0.0/24", namespace=namespace, type="Pool", status=active_status)
        cls.invalid_ipv4 = IPAddress.objects.create(address="10.0.0.1/32", namespace=namespace, status=active_status)

        AAAARecord.objects.create(name="example.com", ip_address=ip_addresses[0], zone=dns_zone)
        AAAARecord.objects.create(name="www.example.com", ip_address=ip_addresses[0], zone=dns_zone)
        AAAARecord.objects.create(name="site.example.com", ip_address=ip_addresses[0], zone=dns_zone)

        cls.create_data = [
            {
                "name": "example.com",
                "ip_address": ip_addresses[1].id,
                "zone": dns_zone.id,
            },
            {
                "name": "www.example.com",
                "ip_address": ip_addresses[1].id,
                "zone": dns_zone.id,
            },
            {
                "name": "site.example.com",
                "ip_address": ip_addresses[1].id,
                "zone": dns_zone.id,
            },
        ]

    def test_create_aaaarecord_with_invalid_ipv4_fails(self):
        """Attempt to create an AAAARecord using an IPv4 address should fail."""
        self.add_permissions("nautobot_dns_models.add_aaaarecord")

        url = reverse("plugins-api:nautobot_dns_models-api:aaaarecord-list")
        data = {
            "name": "invalid.example.com",
            "ip_address": str(self.invalid_ipv4.id),
            "zone": str(self.zone.id),
            "ttl": 3600,
        }

        response = self.client.post(url, data=data, format="json", **self.header)

        self.assertHttpStatus(response, status.HTTP_400_BAD_REQUEST)


class CNAMERecordAPITestCase(APIViewTestCases.APIViewTestCase):
    """Test the Nautobot CNAMERecord API."""

    model = CNAMERecord
    view_namespace = "plugins-api:nautobot_dns_models"
    bulk_update_data = {
        "description": "Example bulk description",
    }
    brief_fields = [
        "name",
        "alias",
    ]

    @classmethod
    def setUpTestData(cls):
        dns_zone = _create_zone(name="example.com")

        CNAMERecord.objects.create(name="www", alias="www.example.com", zone=dns_zone)
        CNAMERecord.objects.create(name="site", alias="site.example.com", zone=dns_zone)
        CNAMERecord.objects.create(name="blog", alias="blog.example.com", zone=dns_zone)

        cls.create_data = [
            {
                "name": "test01",
                "alias": "test01.example.com",
                "zone": dns_zone.id,
            },
            {
                "name": "test02",
                "alias": "test02.example.com",
                "zone": dns_zone.id,
            },
            {
                "name": "test03",
                "alias": "test03.example.com",
                "zone": dns_zone.id,
            },
        ]


class MXRecordAPITestCase(APIViewTestCases.APIViewTestCase):
    """Test the Nautobot MXRecord API."""

    model = MXRecord
    view_namespace = "plugins-api:nautobot_dns_models"
    bulk_update_data = {
        "description": "Example bulk description",
    }
    brief_fields = [
        "name",
        "mail_server",
    ]

    @classmethod
    def setUpTestData(cls):
        dns_zone = _create_zone(name="example.com")

        MXRecord.objects.create(name="mail", mail_server="mail.example.com", zone=dns_zone)
        MXRecord.objects.create(name="mail2", mail_server="mail2.example.com", zone=dns_zone)
        MXRecord.objects.create(name="mail3", mail_server="mail3.example.com", zone=dns_zone)

        cls.create_data = [
            {
                "name": "mail4",
                "mail_server": "mail4.example.com",
                "zone": dns_zone.id,
            },
            {
                "name": "mail5",
                "mail_server": "mail5.example.com",
                "zone": dns_zone.id,
            },
            {
                "name": "mail6",
                "mail_server": "mail6.example.com",
                "zone": dns_zone.id,
            },
        ]


class TXTRecordAPITestCase(APIViewTestCases.APIViewTestCase):
    """Test the Nautobot TXTRecord API."""

    model = TXTRecord
    view_namespace = "plugins-api:nautobot_dns_models"
    bulk_update_data = {
        "description": "Example bulk description",
    }
    brief_fields = [
        "name",
        "text",
    ]

    @classmethod
    def setUpTestData(cls):
        dns_zone = _create_zone(name="example.com")

        TXTRecord.objects.create(name="txt", text="spf-record-01", zone=dns_zone)
        TXTRecord.objects.create(name="txt2", text="spf-record-02", zone=dns_zone)
        TXTRecord.objects.create(name="txt3", text="spf-record-03", zone=dns_zone)

        cls.create_data = [
            {
                "name": "txt4",
                "text": "spf-record-04",
                "zone": dns_zone.id,
            },
            {
                "name": "txt5",
                "text": "spf-record-05",
                "zone": dns_zone.id,
            },
            {
                "name": "txt6",
                "text": "spf-record-06",
                "zone": dns_zone.id,
            },
        ]


class PTRRecordAPITestCase(APIViewTestCases.APIViewTestCase):
    """Test the Nautobot PTRRecord API."""

    model = PTRRecord
    view_namespace = "plugins-api:nautobot_dns_models"
    bulk_update_data = {
        "description": "Example bulk description",
    }
    brief_fields = [
        "name",
        "ptrdname",
    ]

    @classmethod
    def setUpTestData(cls):
        dns_zone = _create_zone(name="example.com")

        PTRRecord.objects.create(name="ptr-record-01", ptrdname="ptr-01", zone=dns_zone)
        PTRRecord.objects.create(name="ptr-record-02", ptrdname="ptr-02", zone=dns_zone)
        PTRRecord.objects.create(name="ptr-record-03", ptrdname="ptr-03", zone=dns_zone)

        cls.create_data = [
            {
                "name": "ptr-record-04",
                "ptrdname": "ptr-04",
                "zone": dns_zone.id,
            },
            {
                "name": "ptr-record-05",
                "ptrdname": "ptr-05",
                "zone": dns_zone.id,
            },
            {
                "name": "ptr-record-06",
                "ptrdname": "ptr-06",
                "zone": dns_zone.id,
            },
        ]


class SRVRecordAPITestCase(APIViewTestCases.APIViewTestCase):
    """Test the Nautobot SRVRecord API."""

    model = SRVRecord
    view_namespace = "plugins-api:nautobot_dns_models"
    bulk_update_data = {
        "description": "Example bulk description",
    }
    brief_fields = [
        "name",
        "target",
    ]

    @classmethod
    def setUpTestData(cls):
        zone = DNSZone.objects.create(name="example.com")
        SRVRecord.objects.create(
            name="_sip._tcp.example.com", priority=10, weight=5, port=5060, target="sip.example.com", zone=zone
        )
        SRVRecord.objects.create(
            name="_ldap._tcp.example.com", priority=20, weight=10, port=389, target="ldap.example.com", zone=zone
        )
        SRVRecord.objects.create(
            name="_xmpp._tcp.example.com", priority=30, weight=15, port=5222, target="xmpp.example.com", zone=zone
        )

        cls.create_data = [
            {
                "name": "_smtp._tcp.example.com",
                "priority": 40,
                "weight": 20,
                "port": 25,
                "target": "smtp.example.com",
                "zone": zone.id,
            },
            {
                "name": "_imap._tcp.example.com",
                "priority": 50,
                "weight": 25,
                "port": 143,
                "target": "imap.example.com",
                "zone": zone.id,
            },
            {
                "name": "_pop3._tcp.example.com",
                "priority": 60,
                "weight": 30,
                "port": 110,
                "target": "pop3.example.com",
                "zone": zone.id,
            },
        ]


class CNAMEExclusivityAPITestCase(APIViewTestCases.APIViewTestCase):
    """API tests for RFC 1912 §2.4 CNAME exclusivity."""

    model = CNAMERecord  # Not used directly but required by base
    view_namespace = "plugins-api:nautobot_dns_models"
    brief_fields = ["name", "alias"]

    @classmethod
    def setUpTestData(cls):
        cls.zone = _create_zone(name="example.com")
        active_status = Status.objects.get(name="Active")
        namespace = Namespace.objects.get(name="Global")
        Prefix.objects.create(prefix="10.22.0.0/24", namespace=namespace, type="Pool", status=active_status)
        cls.ip = IPAddress.objects.create(address="10.22.0.1/32", namespace=namespace, status=active_status)
        # Seed some CNAMEs for base APIViewTestCases
        CNAMERecord.objects.create(name="alpha", alias="alpha.example.com", zone=cls.zone)
        CNAMERecord.objects.create(name="beta", alias="beta.example.com", zone=cls.zone)
        CNAMERecord.objects.create(name="gamma", alias="gamma.example.com", zone=cls.zone)
        cls.create_data = [
            {"name": "delta", "alias": "delta.example.com", "zone": cls.zone.id},
            {"name": "epsilon", "alias": "epsilon.example.com", "zone": cls.zone.id},
            {"name": "zeta", "alias": "zeta.example.com", "zone": cls.zone.id},
        ]

    def test_post_cname_fails_when_arecord_exists(self):
        self.add_permissions("nautobot_dns_models.add_arecord")
        self.add_permissions("nautobot_dns_models.add_cnamerecord")

        # Pre-create A (ip_address field)
        ARecord.objects.create(name="conflict", ip_address=self.ip, zone=self.zone)

        url = reverse("plugins-api:nautobot_dns_models-api:cnamerecord-list")
        data = {"name": "conflict", "alias": "target.example.com", "zone": self.zone.id}
        response = self.client.post(url, data=data, format="json", **self.header)
        self.assertHttpStatus(response, status.HTTP_400_BAD_REQUEST)

    def test_post_arecord_fails_when_cname_exists(self):
        self.add_permissions("nautobot_dns_models.add_arecord")
        self.add_permissions("nautobot_dns_models.add_cnamerecord")

        # Pre-create CNAME
        CNAMERecord.objects.create(name="conflict2", alias="target.example.com", zone=self.zone)

        url = reverse("plugins-api:nautobot_dns_models-api:arecord-list")
        data = {"name": "conflict2", "ip_address": self.ip.id, "zone": self.zone.id}
        response = self.client.post(url, data=data, format="json", **self.header)
        self.assertHttpStatus(response, status.HTTP_400_BAD_REQUEST)

    def test_cname_zone_qualified_allowed(self):
        """A(name="host") does NOT block CNAME(name="host.zone")."""
        self.add_permissions("nautobot_dns_models.add_arecord")
        self.add_permissions("nautobot_dns_models.add_cnamerecord")
        self.add_permissions("nautobot_dns_models.view_dnszone")

        ARecord.objects.create(name="api", ip_address=self.ip, zone=self.zone)
        url = reverse("plugins-api:nautobot_dns_models-api:cnamerecord-list")
        data = {"name": f"api.{self.zone.name}", "alias": "x.example.com", "zone": self.zone.id}
        response = self.client.post(url, data=data, format="json", **self.header)
        self.assertHttpStatus(response, status.HTTP_201_CREATED)

    def test_cname_trailing_dot_zone_qualified_allowed(self):
        """A(name="host") does NOT block CNAME(name="host.zone.") (dot dropped, zone suffix preserved)."""
        self.add_permissions("nautobot_dns_models.add_arecord")
        self.add_permissions("nautobot_dns_models.add_cnamerecord")
        self.add_permissions("nautobot_dns_models.view_dnszone")

        ARecord.objects.create(name="dotapi", ip_address=self.ip, zone=self.zone)
        url = reverse("plugins-api:nautobot_dns_models-api:cnamerecord-list")
        data = {"name": f"dotapi.{self.zone.name}.", "alias": "x.example.com", "zone": self.zone.id}
        response = self.client.post(url, data=data, format="json", **self.header)
        self.assertHttpStatus(response, status.HTTP_201_CREATED)

    def test_arecord_zone_qualified_allowed(self):
        """CNAME(name="host") does NOT block A(name="host.zone")."""
        self.add_permissions("nautobot_dns_models.add_arecord")
        self.add_permissions("nautobot_dns_models.add_cnamerecord")
        self.add_permissions("nautobot_dns_models.view_dnszone")
        self.add_permissions("ipam.view_ipaddress")

        CNAMERecord.objects.create(name="reverseapi", alias="x.example.com", zone=self.zone)
        url = reverse("plugins-api:nautobot_dns_models-api:arecord-list")
        data = {"name": f"reverseapi.{self.zone.name}", "ip_address": self.ip.id, "zone": self.zone.id}
        response = self.client.post(url, data=data, format="json", **self.header)
        self.assertHttpStatus(response, status.HTTP_201_CREATED)

    @override_config(nautobot_dns_models__CNAME_RESTRICTION_ENABLED=False)
    def test_opt_out_allows_coexistence(self):
        self.add_permissions("nautobot_dns_models.add_arecord")
        self.add_permissions("nautobot_dns_models.add_cnamerecord")
        self.add_permissions("nautobot_dns_models.view_dnszone")
        self.add_permissions("ipam.view_ipaddress")

        # Create A
        url_a = reverse("plugins-api:nautobot_dns_models-api:arecord-list")
        data_a = {"name": "opt", "ip_address": self.ip.id, "zone": self.zone.id}
        response = self.client.post(url_a, data=data_a, format="json", **self.header)
        self.assertHttpStatus(response, status.HTTP_201_CREATED)

        # Create CNAME with same name
        url_c = reverse("plugins-api:nautobot_dns_models-api:cnamerecord-list")
        data_c = {"name": "opt", "alias": "opt.example.com", "zone": self.zone.id}
        response = self.client.post(url_c, data=data_c, format="json", **self.header)
        self.assertHttpStatus(response, status.HTTP_201_CREATED)
