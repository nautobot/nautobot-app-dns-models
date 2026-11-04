"""Test Data Validation Engine rules for nautobot_dns_models."""

from constance.test import override_config
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from nautobot.apps.testing import TestCase
from nautobot.data_validation.models import DataCompliance
from nautobot.extras.registry import registry

from nautobot_dns_models.custom_validators import TXTRecordRFC1035LengthRule
from nautobot_dns_models.models import DNSZone, TXTRecord


class TXTRecordRFC1035LengthRuleTestCase(TestCase):
    """Test the TXT RDATA length rule's registration and enforce/audit behavior."""

    @classmethod
    def setUpTestData(cls):
        cls.zone = DNSZone.objects.create(name="example.com")

    def _compliance_results(self, record):
        return DataCompliance.objects.filter(
            compliance_class_name=TXTRecordRFC1035LengthRule.name,
            content_type=ContentType.objects.get_for_model(TXTRecord),
            object_id=record.pk,
        )

    def test_rule_is_registered_with_the_data_validation_engine(self):
        self.assertIn(TXTRecordRFC1035LengthRule, registry["plugin_custom_validators"]["nautobot_dns_models.txtrecord"])

    def test_enforces_when_validation_level_is_wire_format(self):
        record = TXTRecord(name="txt", text='"' + "a" * 300 + '"', zone=self.zone)
        self.assertTrue(TXTRecordRFC1035LengthRule(record).enforce)
        with self.assertRaises(ValidationError) as context:
            record.full_clean()
        self.assertIn("text", context.exception.message_dict)

    @override_config(nautobot_dns_models__DNS_VALIDATION_LEVEL="none")
    def test_records_non_compliance_without_blocking_when_validation_disabled(self):
        record = TXTRecord(name="txt", text='"' + "a" * 300 + '"', zone=self.zone)
        record.validated_save()  # Should not raise

        self.assertTrue(self._compliance_results(record).filter(validated_attribute="text", valid=False).exists())

    @override_config(nautobot_dns_models__DNS_VALIDATION_LEVEL="none")
    def test_records_parse_errors_as_non_compliance_when_validation_disabled(self):
        record = TXTRecord(name="txt", text='"abc', zone=self.zone)
        record.validated_save()  # Should not raise

        result = self._compliance_results(record).get(validated_attribute="text")
        self.assertFalse(result.valid)
        self.assertIn("Unterminated quoted character-string", result.message)

    def test_records_compliance_for_a_valid_record(self):
        record = TXTRecord(name="txt", text="v=spf1 -all", zone=self.zone)
        record.validated_save()

        self.assertTrue(self._compliance_results(record).filter(validated_attribute="__all__", valid=True).exists())

    def test_audit_only_mode_does_not_raise(self):
        """The Data Compliance job sets `enforce = False` on the instance to audit existing records."""
        record = TXTRecord(name="txt", text='"' + "a" * 300 + '"', zone=self.zone)
        rule = TXTRecordRFC1035LengthRule(record)
        rule.enforce = False
        rule.clean()  # Should not raise

    @override_config(nautobot_dns_models__DNS_VALIDATION_LEVEL="none")
    def test_truncates_long_values_stored_in_compliance_results(self):
        """`DataCompliance.validated_attribute_value` is 255 characters; TXT content can be far longer."""
        record = TXTRecord(name="txt", text="a" * 66000, zone=self.zone)
        record.validated_save()

        result = self._compliance_results(record).get(validated_attribute="text")
        self.assertFalse(result.valid)
        self.assertEqual(len(result.validated_attribute_value), 255)

    def test_long_valid_value_after_a_previous_failure(self):
        """A record fixed to a long, valid value must not fail to record its compliance result."""
        with override_config(nautobot_dns_models__DNS_VALIDATION_LEVEL="none"):
            record = TXTRecord(name="dkim", text='"' + "a" * 300 + '"', zone=self.zone)
            record.validated_save()

        record.text = "v=DKIM1; k=rsa; p=" + "A" * 582
        record.validated_save()

        self.assertTrue(self._compliance_results(record).get(validated_attribute="text").valid)
