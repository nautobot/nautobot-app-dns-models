"""Unit tests for views."""

from django.contrib.auth import get_user_model
from nautobot.apps.testing import ViewTestCases

from nautobot_dns_models import models
from nautobot_dns_models.models import DNSZoneModel, NSRecordModel
from nautobot_dns_models.tests import fixtures

User = get_user_model()

# TODO add views tests

# class DnsZoneModelViewTest(ViewTestCases.PrimaryObjectViewTestCase):
#     # pylint: disable=too-many-ancestors
#     """Test the DnsZoneModel views."""

#     model = models.DNSZoneModel

#     test_bulk_edit_objects_with_constrained_permission = None
#     test_bulk_edit_objects_with_permission = None
#     test_bulk_import_objects_with_permission = None
#     test_bulk_import_objects_with_constrained_permission = None

#     @classmethod
#     def setUpTestData(cls):
#         DNSZoneModel.objects.create(
#             name="example_one.com",
#             filename="test one",
#             soa_mname="auth-server",
#             soa_rname="admin@example_one.com",
#             soa_refresh=86400,
#             soa_retry=7200,
#             soa_expire=3600000,
#             soa_serial=0,
#             soa_minimum=172800,
#         )
#         DNSZoneModel.objects.create(
#             name="example_two.com",
#             filename="test two",
#             soa_mname="auth-server",
#             soa_rname="admin@example_two.com",
#             soa_refresh=86400,
#             soa_retry=7200,
#             soa_expire=3600000,
#             soa_serial=0,
#             soa_minimum=172800,
#         )
#         DNSZoneModel.objects.create(
#             name="example_three.com",
#             filename="test three",
#             soa_mname="auth-server",
#             soa_rname="admin@example_three.com",
#             soa_refresh=86400,
#             soa_retry=7200,
#             soa_expire=3600000,
#             soa_serial=0,
#             soa_minimum=172800,
#         )
#         # DNSZoneModel.objects.create(name="Test Two")
#         # DNSZoneModel.objects.create(name="Test Three")

#         cls.form_data = {
#             "name": "Test 1",
#             "description": "Initial model",
#         }

#         cls.csv_data = (
#             "name, description, filename, soa_mname, soa_rname, soa_refresh, soa_retry, soa_expire, soa_serial, soa_minimum",
#             "Test 3, Description 3, filename 3, auth-server, admin@example_three.com, 86400, 7200, 3600000, 0, 172800",
#         )

#         cls.bulk_edit_data = {"description": "Bulk edit views"}

# def test_bulk_import_objects_with_constrained_permission(self):
#     """Auto-generated model does not implement `bulk_import`."""

# def test_bulk_import_objects_with_permission(self):
#     """Auto-generated model does not implement `bulk_import`."""

# def test_bulk_import_objects_without_permission(self):
#     """Auto-generated model does not implement `bulk_import`."""

# def test_bulk_import_objects_with_permission_csv_file(self):
#     """Auto-generated model does not implement `bulk_import`."""

# def test_has_advanced_tab(self):
#     """Auto-generated model does not implement an advanced tab."""


class NSRecordModelViewTest(ViewTestCases.PrimaryObjectViewTestCase):
    # pylint: disable=too-many-ancestors
    """Test the NSRecordModel views."""

    model = NSRecordModel
    # test_bulk_edit_objects_with_constrained_permission = None
    # test_bulk_edit_objects_with_permission = None
    test_bulk_import_objects_with_permission = None
    test_bulk_import_objects_with_constrained_permission = None

    @classmethod
    def setUpTestData(cls):
        zone = DNSZoneModel.objects.create(
            name="example_one.com",
        )

        NSRecordModel.objects.create(
            name="primary",
            server="example-server.com.",
            zone=zone,
        )
        NSRecordModel.objects.create(
            name="secondary",
            server="example-server.com.",
            zone=zone,
        )
        NSRecordModel.objects.create(
            name="tertiary",
            server="example-server.com.",
            zone=zone,
        )

        cls.form_data = {
            "name": "test record",
            "server": "test server",
            "zone": zone.pk,
        }

        cls.csv_data = (
            "name,server,zone",
            f"Test 3,server 3,{zone.name}",
        )

        cls.bulk_edit_data = {"description": "Bulk edit views"}
