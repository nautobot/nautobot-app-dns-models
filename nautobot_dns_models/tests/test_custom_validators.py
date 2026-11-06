"""Test the Data Validation Engine rules for nautobot_dns_models."""

from django.contrib.contenttypes.models import ContentType
from nautobot.apps.testing import TestCase
from nautobot.data_validation.models import DataCompliance
from nautobot.extras.models import Status
from nautobot.extras.registry import registry
from nautobot.ipam.models import IPAddress, Namespace, Prefix

from nautobot_dns_models import custom_validators
from nautobot_dns_models.models import ARecord, CNAMERecord, DNSDelegation, DNSZone, NSRecord, TXTRecord


def _create_zone(name):
    return DNSZone.objects.create(
        name=name, filename=f"{name}.zone", soa_mname="ns1.example.net", soa_rname="hostmaster@example.net"
    )


class DNSComplianceRuleTestCase(TestCase):
    """Shared fixtures: `example.com` delegates `apps` to an in-domain and an out-of-bailiwick name server."""

    @classmethod
    def setUpTestData(cls):
        status = Status.objects.get(name="Active")
        namespace = Namespace.objects.get(name="Global")
        Prefix.objects.create(prefix="192.0.2.0/24", namespace=namespace, type="Pool", status=status)
        cls.ip_10 = IPAddress.objects.create(address="192.0.2.10/32", namespace=namespace, status=status)
        cls.ip_11 = IPAddress.objects.create(address="192.0.2.11/32", namespace=namespace, status=status)
        cls.zone = _create_zone("example.com")

    def _create_delegation(self):
        NSRecord.objects.create(name="apps", server="ns1.apps.example.com", zone=self.zone)
        NSRecord.objects.create(name="apps", server="ns2.other.net", zone=self.zone)
        delegation = DNSDelegation(zone=self.zone, name="apps")
        delegation.validated_save()
        return delegation

    def _result(self, obj, rule_name):
        """Return the stored result for `obj` and rule `rule_name`, re-running the rules first."""
        obj.validated_save()
        return DataCompliance.objects.get(
            compliance_class_name=rule_name,
            content_type=ContentType.objects.get_for_model(obj),
            object_id=obj.pk,
            validated_attribute="__all__",
        )

    def assert_compliant(self, obj, rule_name):
        """Assert that `obj` passes rule `rule_name`."""
        result = self._result(obj, rule_name)
        self.assertTrue(result.valid, result.message)

    def assert_not_compliant(self, obj, rule_name, message_fragment):
        """Assert that `obj` fails rule `rule_name` with a message containing `message_fragment`."""
        self._result(obj, rule_name)
        result = DataCompliance.objects.get(
            compliance_class_name=rule_name,
            content_type=ContentType.objects.get_for_model(obj),
            object_id=obj.pk,
            validated_attribute="name",
        )
        self.assertFalse(result.valid)
        self.assertIn(message_fragment, result.message)


class RuleRegistrationTestCase(DNSComplianceRuleTestCase):
    """Test how the rules are registered."""

    def test_every_rule_is_registered_and_audit_only(self):
        registered = registry["plugin_custom_validators"]
        for rule in custom_validators.custom_validators:
            with self.subTest(rule=rule.name):
                self.assertIn(rule, registered[rule.model])
                self.assertFalse(rule.enforce)

    def test_a_failing_rule_does_not_block_the_save(self):
        delegation = DNSDelegation(zone=self.zone, name="empty")
        delegation.validated_save()
        self.assertTrue(DNSDelegation.objects.filter(pk=delegation.pk).exists())


class DNSDelegationRulesTestCase(DNSComplianceRuleTestCase):
    """Test the rules that check a delegation."""

    def test_name_servers_rule(self):
        name = custom_validators.DNSDelegationNameServersRule.name
        empty = DNSDelegation.objects.create(zone=self.zone, name="empty")
        self.assert_not_compliant(empty, name, "No NS records")
        self.assert_compliant(self._create_delegation(), name)

    def test_in_domain_glue_rule(self):
        name = custom_validators.DNSDelegationGlueRule.name
        delegation = self._create_delegation()
        self.assert_not_compliant(delegation, name, "ns1.apps.example.com")

        ARecord.objects.create(name="ns1.apps", ip_address=self.ip_10, zone=self.zone)
        self.assert_compliant(delegation, name)

    def test_child_glue_rule(self):
        name = custom_validators.DNSDelegationChildGlueRule.name
        delegation = self._create_delegation()
        ARecord.objects.create(name="ns1.apps", ip_address=self.ip_10, zone=self.zone)
        self.assert_compliant(delegation, name)  # No child zone in Nautobot: nothing to compare.

        child = _create_zone("apps.example.com")
        ARecord.objects.create(name="ns1", ip_address=self.ip_11, zone=child)
        self.assert_not_compliant(delegation, name, "ns1.apps.example.com")

        ARecord.objects.filter(zone=child).update(ip_address=self.ip_10)
        self.assert_compliant(delegation, name)

    def test_child_name_servers_rule(self):
        name = custom_validators.DNSDelegationChildNameServersRule.name
        delegation = self._create_delegation()
        child = _create_zone("apps.example.com")
        NSRecord.objects.create(name="@", server="ns1.apps.example.com.", zone=child)
        self.assert_not_compliant(delegation, name, "Only in the parent: ns2.other.net")

        NSRecord.objects.create(name="@", server="NS2.other.net", zone=child)
        self.assert_compliant(delegation, name)


class DNSZoneDelegatedRuleTestCase(DNSComplianceRuleTestCase):
    """Test the rule that checks a zone is delegated from its parent."""

    def test_zone_below_another_zone_needs_a_delegation(self):
        name = custom_validators.DNSZoneDelegatedRule.name
        child = _create_zone("apps.example.com")
        self.assert_not_compliant(child, name, "has no NS records at `apps`")

        self._create_delegation()
        self.assert_compliant(child, name)

    def test_ns_records_at_the_owner_name_mark_the_cut(self):
        child = _create_zone("apps.example.com")
        NSRecord.objects.create(name="apps", server="ns1.example.com", zone=self.zone)
        self.assert_compliant(child, custom_validators.DNSZoneDelegatedRule.name)

    def test_zone_renamed_below_its_old_name_is_not_its_own_parent(self):
        zone = _create_zone("lab.example.net")
        zone.name = "x.lab.example.net"
        self.assert_compliant(zone, custom_validators.DNSZoneDelegatedRule.name)

    def test_zone_below_another_cut_in_the_parent_is_not_reported(self):
        """`example.com` delegates `apps` outside Nautobot, which delegates `dev.apps.example.com` back to Nautobot."""
        NSRecord.objects.create(name="apps", server="ns1.partner.net", zone=self.zone)
        DNSDelegation(zone=self.zone, name="apps").validated_save()
        self.assert_compliant(_create_zone("dev.apps.example.com"), custom_validators.DNSZoneDelegatedRule.name)

    def test_zone_below_a_cut_marked_only_by_ns_records_is_not_reported(self):
        NSRecord.objects.create(name="apps", server="ns1.partner.net", zone=self.zone)
        self.assert_compliant(_create_zone("dev.apps.example.com"), custom_validators.DNSZoneDelegatedRule.name)

    def test_zone_two_labels_below_the_parent_without_any_cut_is_reported(self):
        self.assert_not_compliant(
            _create_zone("dev.apps.example.com"),
            custom_validators.DNSZoneDelegatedRule.name,
            "has no NS records at `dev.apps`",
        )

    def test_zone_without_a_parent_is_compliant(self):
        self.assert_compliant(self.zone, custom_validators.DNSZoneDelegatedRule.name)


class RecordNotOccludedRuleTestCase(DNSComplianceRuleTestCase):
    """Test the rules that check records are not hidden below a zone cut."""

    def test_records_below_a_cut_are_reported(self):
        self._create_delegation()
        below = TXTRecord.objects.create(name="www.apps", text="hidden", zone=self.zone)
        at_cut = ARecord.objects.create(name="apps", ip_address=self.ip_11, zone=self.zone)
        self.assert_not_compliant(below, "TXT Record Not Below a Zone Cut", "zone cut at apps.example.com")
        self.assert_not_compliant(at_cut, "A Record Not Below a Zone Cut", "zone cut at apps.example.com")

    def test_ns_at_the_cut_and_glue_are_exempt(self):
        self._create_delegation()
        glue = ARecord.objects.create(name="ns1.apps", ip_address=self.ip_10, zone=self.zone)
        ns_at_cut = NSRecord.objects.get(zone=self.zone, server="ns1.apps.example.com")
        self.assert_compliant(glue, "A Record Not Below a Zone Cut")
        self.assert_compliant(ns_at_cut, "NS Record Not Below a Zone Cut")

    def test_records_outside_any_cut_are_compliant(self):
        self._create_delegation()
        record = CNAMERecord.objects.create(name="www", alias="web.example.net", zone=self.zone)
        self.assert_compliant(record, "CNAME Record Not Below a Zone Cut")
