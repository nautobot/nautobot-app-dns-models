"""Test the GraphQL schema this app contributes."""

from graphene_django.settings import graphene_settings
from graphql import parse, validate
from nautobot.apps.graphql import execute_query
from nautobot.apps.testing import TestCase
from nautobot.extras.models import Status
from nautobot.ipam.models import IPAddress, Namespace, Prefix

from nautobot_dns_models.choices import DNSZoneTypeChoices
from nautobot_dns_models.models import DNSForwarder
from nautobot_dns_models.tests.fixtures import create_zone


class GraphQLQueryMixin:
    """Runs a query as the test user, holding the schema to what the query asks of it."""

    def run_query(self, query, **variables):
        """Return the data `query` selects, failing if the schema does not accept it or execution errors.

        Validated separately because `execute_query` parses without validating, so a field the schema does
        not define would otherwise be dropped from the response rather than reported.
        """
        schema_errors = validate(graphene_settings.SCHEMA.graphql_schema, parse(query))
        self.assertEqual(schema_errors, [])

        result = execute_query(query, variables=variables or None, user=self.user)
        self.assertIsNone(result.errors)
        return result.data


class DNSZoneTestCase(GraphQLQueryMixin, TestCase):
    """Tests the catalog membership of zones as read over the type core generates for `DNSZone`."""

    ZONES_QUERY = """
        query ($name: [String]) {
            dns_zones(name: $name) {
                name
                member_label
                catalog_zone {
                    name
                }
            }
        }
    """

    @classmethod
    def setUpTestData(cls):
        cls.catalog_zone = create_zone("catalog.example", type=DNSZoneTypeChoices.TYPE_CATALOG)
        cls.member_zone = create_zone("member.example", catalog_zone=cls.catalog_zone)
        cls.solo_zone = create_zone("solo.example")

    def test_catalog_zone_names_the_catalog_a_zone_belongs_to(self):
        """GraphQL returns a member zone's catalog zone and member label."""
        self.add_permissions("nautobot_dns_models.view_dnszone")

        zones = self.run_query(self.ZONES_QUERY, name=["member.example"])["dns_zones"]

        self.assertEqual(zones[0]["catalog_zone"], {"name": "catalog.example"})
        self.assertEqual(zones[0]["member_label"], self.member_zone.member_label)

    def test_catalog_zone_is_null_for_a_zone_in_no_catalog(self):
        """GraphQL returns a null catalog zone for a zone in no catalog."""
        self.add_permissions("nautobot_dns_models.view_dnszone")

        zones = self.run_query(self.ZONES_QUERY, name=["solo.example"])["dns_zones"]

        self.assertIsNone(zones[0]["catalog_zone"])


class DNSForwarderTestCase(GraphQLQueryMixin, TestCase):
    """Tests the address a forwarder reports over GraphQL."""

    FORWARDERS_QUERY = """
        query {
            dns_forwarders {
                name
                effective_address
            }
        }
    """

    @classmethod
    def setUpTestData(cls):
        status = Status.objects.get(name="Active")
        namespace = Namespace.objects.get(name="Global")
        Prefix.objects.create(prefix="192.0.2.0/24", namespace=namespace, type="Pool", status=status)
        ip_address = IPAddress.objects.create(address="192.0.2.53/32", namespace=namespace, status=status)
        DNSForwarder.objects.create(name="Corp resolver", ip_address=ip_address)
        DNSForwarder.objects.create(name="Quad9", address="9.9.9.9")

    def test_effective_address_comes_from_either_source(self):
        """GraphQL returns the IPAM address or the literal address as `effective_address`."""
        self.add_permissions("nautobot_dns_models.view_dnsforwarder")

        forwarders = self.run_query(self.FORWARDERS_QUERY)["dns_forwarders"]

        self.assertEqual(
            {forwarder["name"]: forwarder["effective_address"] for forwarder in forwarders},
            {"Corp resolver": "192.0.2.53", "Quad9": "9.9.9.9"},
        )
