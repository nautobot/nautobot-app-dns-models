"""Test DnsZoneModel."""

from django.test import TestCase
import unittest
from unittest.mock import patch

from nautobot_dns_models.models import (
    ARecordModel,
    AAAARecordModel,
    CNAMERecordModel,
    DnsZoneModel,
    MXRecordModel,
    NSRecordModel,
    TXTRecordModel,
    PTRRecordModel,
)


class DnsZoneModelTest(TestCase):
    """Test DnsZoneModel."""

    def test_create_dnszonemodel_only_required(self):
        """Create with only required fields, and validate null description and __str__."""
        dnszonemodel = DnsZoneModel.objects.create(name="Development", slug="development")
        self.assertEqual(dnszonemodel.name, "Development")
        self.assertEqual(dnszonemodel.description, "")
        self.assertEqual(str(dnszonemodel), "Development")
        self.assertEqual(dnszonemodel.slug, "development")

    def test_create_dnszonemodel_all_fields_success(self):
        """Create DnsZoneModel with all fields."""
        dnszonemodel = DnsZoneModel.objects.create(
            name="Development", slug="development", description="Development Test"
        )
        self.assertEqual(dnszonemodel.name, "Development")
        self.assertEqual(dnszonemodel.slug, "development")
        self.assertEqual(dnszonemodel.description, "Development Test")

    def test_get_absolute_url(self):
        dns_zone_model = DnsZoneModel(name="example.com")
        self.assertEqual(dns_zone_model.get_absolute_url(), "/plugins/nautobot_dns_models/dnszonemodel/1/")


class DnsZoneModelUnitTest(unittest.TestCase):
    def test_get_absolute_url(self):
        with patch("nautobot.dns.models.reverse") as mock_reverse:
            mock_reverse.return_value = "/plugins/nautobot_dns_models/dnszonemodel/1/"
            dns_zone_model = DnsZoneModel(name="example.com")
            self.assertEqual(dns_zone_model.get_absolute_url(), "/plugins/nautobot_dns_models/dnszonemodel/1/")


class NSRecordModelTest(TestCase):
    def test_get_absolute_url(self):
        ns_record_model = NSRecordModel(name="example.com")
        self.assertEqual(ns_record_model.get_absolute_url(), "/plugins/nautobot_dns_models/nsrecordmodel/1/")


class NSRecordModelUnitTest(unittest.TestCase):
    def test_get_absolute_url(self):
        with patch("nautobot.dns.models.reverse") as mock_reverse:
            mock_reverse.return_value = "/plugins/nautobot_dns_models/nsrecordmodel/1/"
            ns_record_model = NSRecordModel(name="example.com")
            self.assertEqual(ns_record_model.get_absolute_url(), "/plugins/nautobot_dns_models/nsrecordmodel/1/")


class ARecordModelTest(TestCase):
    def test_get_absolute_url(self):
        arecord_model = ARecordModel(name="example.com")
        self.assertEqual(arecord_model.get_absolute_url(), "/plugins/nautobot_dns_models/arecordmodel/1/")


class AAAARecordModelTest(TestCase):
    def test_get_absolute_url(self):
        aaaarecord_model = AAAARecordModel(name="example.com")
        self.assertEqual(aaaarecord_model.get_absolute_url(), "/plugins/nautobot_dns_models/aaaarecordmodel/1/")


class CNAMERecordModelTest(TestCase):
    def test_get_absolute_url(self):
        cname_record_model = CNAMERecordModel(name="example.com")
        self.assertEqual(cname_record_model.get_absolute_url(), "/plugins/nautobot_dns_models/cnamerecordmodel/1/")


class MXRecordModelTest(TestCase):
    def test_get_absolute_url(self):
        mx_record_model = MXRecordModel(name="example.com")
        self.assertEqual(mx_record_model.get_absolute_url(), "/plugins/nautobot_dns_models/mxrecordmodel/1/")


class TXTRecordModelTest(TestCase):
    def test_get_absolute_url(self):
        txt_record_model = TXTRecordModel(name="example.com")
        self.assertEqual(txt_record_model.get_absolute_url(), "/plugins/nautobot_dns_models/txtrecordmodel/1/")


class PTRRecordModelTest(TestCase):
    def test_get_absolute_url(self):
        ptr_record_model = PTRRecordModel(name="example.com")
        self.assertEqual(ptr_record_model.get_absolute_url(), "/plugins/nautobot_dns_models/ptrrecordmodel/1/")


class ARecordModelUnitTest(unittest.TestCase):
    def test_get_absolute_url(self):
        with patch("nautobot.dns.models.reverse") as mock_reverse:
            mock_reverse.return_value = "/plugins/nautobot_dns_models/arecordmodel/1/"
            arecord_model = ARecordModel(name="example.com")
            self.assertEqual(arecord_model.get_absolute_url(), "/plugins/nautobot_dns_models/arecordmodel/1/")


class AAAARecordModelUnitTest(unittest.TestCase):
    def test_get_absolute_url(self):
        with patch("nautobot.dns.models.reverse") as mock_reverse:
            mock_reverse.return_value = "/plugins/nautobot_dns_models/aaaarecordmodel/1/"
            aaaarecord_model = AAAARecordModel(name="example.com")
            self.assertEqual(aaaarecord_model.get_absolute_url(), "/plugins/nautobot_dns_models/aaaarecordmodel/1/")


class CNAMERecordModelUnitTest(unittest.TestCase):
    def test_get_absolute_url(self):
        with patch("nautobot.dns.models.reverse") as mock_reverse:
            mock_reverse.return_value = "/plugins/nautobot_dns_models/cnamerecordmodel/1/"
            cname_record_model = CNAMERecordModel(name="example.com")
            self.assertEqual(cname_record_model.get_absolute_url(), "/plugins/nautobot_dns_models/cnamerecordmodel/1/")


class MXRecordModelUnitTest(unittest.TestCase):
    def test_get_absolute_url(self):
        with patch("nautobot.dns.models.reverse") as mock_reverse:
            mock_reverse.return_value = "/plugins/nautobot_dns_models/mxrecordmodel/1/"
            mx_record_model = MXRecordModel(name="example.com")
            self.assertEqual(mx_record_model.get_absolute_url(), "/plugins/nautobot_dns_models/mxrecordmodel/1/")


class TXTRecordModelUnitTest(unittest.TestCase):
    def test_get_absolute_url(self):
        with patch("nautobot.dns.models.reverse") as mock_reverse:
            mock_reverse.return_value = "/plugins/nautobot_dns_models/txtrecordmodel/1/"
            txt_record_model = TXTRecordModel(name="example.com")
            self.assertEqual(txt_record_model.get_absolute_url(), "/plugins/nautobot_dns_models/txtrecordmodel/1/")


class PTRRecordModelUnitTest(unittest.TestCase):
    def test_get_absolute_url(self):
        with patch("nautobot.dns.models.reverse") as mock_reverse:
            mock_reverse.return_value = "/plugins/nautobot_dns_models/ptrrecordmodel/1/"
            ptr_record_model = PTRRecordModel(name="example.com")
            self.assertEqual(ptr_record_model.get_absolute_url(), "/plugins/nautobot_dns_models/ptrrecordmodel/1/")
