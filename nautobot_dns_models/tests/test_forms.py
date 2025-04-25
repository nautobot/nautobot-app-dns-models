"""Test dnszonemodel forms."""

from django.test import TestCase

from nautobot_dns_models import forms


class DnsZoneModelTest(TestCase):
    """Test DnsZoneModel forms."""

    def test_specifying_all_fields_success(self):
        form = forms.DnsZoneModelForm(
            data={
                "name": "Development",
                "description": "Development Testing",
            }
        )
        self.assertTrue(form.is_valid())
        self.assertTrue(form.save())

    def test_specifying_only_required_success(self):
        form = forms.DnsZoneModelForm(
            data={
                "name": "Development",
            }
        )
        self.assertTrue(form.is_valid())
        self.assertTrue(form.save())

    def test_validate_name_dnszonemodel_is_required(self):
        form = forms.DnsZoneModelForm(data={"description": "Development Testing"})
        self.assertFalse(form.is_valid())
        self.assertIn("This field is required.", form.errors["name"])
