"""Data Validation Engine rules for nautobot_dns_models.

Registered automatically through `NautobotAppConfig.custom_validators`. Every rule here is audit-only: it records its
result under Data Compliance and never blocks a save. The rules compare several objects, so a result can go stale when
a related object changes; the core job "Run Registered Data Compliance Rules" refreshes all results.
"""

from nautobot.apps.models import ComplianceError, DataComplianceRule

from nautobot_dns_models.choices import NameServerBailiwickChoices
from nautobot_dns_models.models import (
    DNSDelegation,
    DNSZone,
    NSRecord,
    get_address_records,
)
from nautobot_dns_models.utils import dns_name_key, is_subdomain, owner_fqdn, relative_owner_name


class DNSComplianceRule(DataComplianceRule):  # pylint: disable=abstract-method
    """Base class for this app's audit-only rules."""

    enforce = False

    def __init__(self, obj):
        """Keep the validated object; the validator context key is `object` in Nautobot 3.1 and `obj` from 3.2."""
        super().__init__(obj)
        self.instance = obj


def _address_set(records):
    return {str(record.ip_address.host) for record in records}


def _in_domain_servers(delegation):
    return sorted(
        {
            ns_record.server
            for ns_record in delegation.ns_records
            if delegation.classify_name_server(ns_record.server) == NameServerBailiwickChoices.IN_DOMAIN
        }
    )


class DNSDelegationNameServersRule(DNSComplianceRule):
    """A delegation needs NS records at its owner name (RFC 1034 §4.2.1)."""

    name = "DNS Delegation Has Name Servers"
    model = "nautobot_dns_models.dnsdelegation"

    def audit(self):
        """Report a delegation with no NS records in the parent zone."""
        if not self.instance.ns_records.exists():
            raise ComplianceError(
                {
                    "name": "No NS records exist at this owner name in the parent zone, so the zone cut has no name servers."
                }
            )


class DNSDelegationGlueRule(DNSComplianceRule):
    """An in-domain name server needs glue address records in the parent zone (RFC 9471 §2.1)."""

    name = "DNS Delegation In-Domain Glue"
    model = "nautobot_dns_models.dnsdelegation"

    def audit(self):
        """Report in-domain name servers with no A or AAAA record in the parent zone."""
        missing = [server for server in _in_domain_servers(self.instance) if not self.instance.get_glue_records(server)]
        if missing:
            raise ComplianceError(
                {
                    "name": (
                        f"In-domain name servers without glue A/AAAA records in zone {self.instance.zone.name}: "
                        f"{', '.join(missing)}."
                    )
                }
            )


class DNSDelegationChildGlueRule(DNSComplianceRule):
    """Glue in the parent zone should match the addresses the child zone publishes for its name servers."""

    name = "DNS Delegation Glue Matches Child Zone"
    model = "nautobot_dns_models.dnsdelegation"

    def audit(self):
        """Report in-domain name servers whose glue differs from the child zone's own A/AAAA records."""
        child_zone = self.instance.get_child_zone()
        if child_zone is None:
            return
        mismatched = [
            server
            for server in _in_domain_servers(self.instance)
            if _address_set(self.instance.get_glue_records(server))
            != _address_set(get_address_records(child_zone, server))
        ]
        if mismatched:
            raise ComplianceError(
                {
                    "name": f"Glue addresses differ from those in child zone {child_zone.name} for: {', '.join(mismatched)}."
                }
            )


class DNSDelegationChildNameServersRule(DNSComplianceRule):
    """The parent's NS records for a cut should match the child zone's apex NS records (RFC 1034 §4.2.2)."""

    name = "DNS Delegation Name Servers Match Child Zone"
    model = "nautobot_dns_models.dnsdelegation"

    def audit(self):
        """Report a difference between the parent's NS set and the child zone's apex NS set."""
        child_zone = self.instance.get_child_zone()
        if child_zone is None:
            return
        parent_servers = {dns_name_key(server) for server in self.instance.ns_records.values_list("server", flat=True)}
        child_servers = {
            dns_name_key(server)
            for server in NSRecord.objects.filter(zone=child_zone, name__in=["@", ""]).values_list("server", flat=True)
        }
        if parent_servers != child_servers:
            only_parent = ", ".join(sorted(parent_servers - child_servers)) or "none"
            only_child = ", ".join(sorted(child_servers - parent_servers)) or "none"
            raise ComplianceError(
                {
                    "name": (
                        f"NS records differ from the apex NS records of child zone {child_zone.name}. "
                        f"Only in the parent: {only_parent}. Only in the child: {only_child}."
                    )
                }
            )


class DNSZoneDelegatedRule(DNSComplianceRule):
    """A zone below another zone in the same DNS View should be delegated from it (RFC 1034 §4.2.1).

    The cut is marked by NS records in the parent zone at the child's owner name. A `DNSDelegation` there counts as
    well, since it states the cut even before its NS records exist.

    A zone below a different cut in the parent zone is not checked. For example, with `example.com` delegating
    `apps` and `dev.apps.example.com` in Nautobot, `dev.apps.example.com` is delegated from `apps.example.com`, a zone
    outside Nautobot; `example.com` must not hold its NS records.
    """

    name = "DNS Zone Delegated From Parent"
    model = "nautobot_dns_models.dnszone"

    def audit(self):
        """Report a zone whose parent zone has neither NS records nor a delegation at the zone's name."""
        zone = self.instance
        # Exclude this zone: while a renamed zone is validated, the database still holds its old name.
        parent = DNSZone.get_enclosing_zone(zone.name, zone.dns_view_id, exclude_pk=zone.pk)
        if parent is None:
            return
        owner = relative_owner_name(dns_name_key(zone.name), dns_name_key(parent.name))
        if self._has_cut(parent, owner):
            return
        if any(self._has_cut(parent, intermediate) for intermediate in self._intermediate_owners(owner)):
            # Delegated by a zone between `parent` and this one that is not in Nautobot, so not checkable here.
            return
        raise ComplianceError(
            {
                "name": (
                    f"Parent zone {parent.name} has no NS records at `{owner}` marking the zone cut, so resolvers "
                    f"following referrals from {parent.name} cannot find this zone. Add NS records or a DNS "
                    f"delegation for `{owner}` in {parent.name}."
                )
            }
        )

    @staticmethod
    def _has_cut(parent, owner):
        """Return whether `parent` marks a zone cut at `owner`, with NS records or a DNS delegation."""
        return (
            NSRecord.objects.filter(zone=parent, name__iexact=owner).exists()
            or DNSDelegation.objects.filter(zone=parent, name__iexact=owner).exists()
        )

    @staticmethod
    def _intermediate_owners(owner):
        """Yield the owner names strictly between the parent zone apex and `owner`; `dev.apps` yields `apps`."""
        labels = owner.split(".")
        for index in range(1, len(labels)):
            yield ".".join(labels[index:])


class RecordNotOccludedRule(DNSComplianceRule):  # pylint: disable=abstract-method
    """A record at or below a zone cut is not authoritative data of its zone (RFC 1034 §4.2.1).

    NS records at the cut and glue address records for the zone's delegations are exempt.
    """

    def audit(self):
        """Report a record whose owner name is at or below a delegation in its zone."""
        record = self.instance
        zone = record.zone
        owner_key = dns_name_key(owner_fqdn(record.name, zone.name))
        delegations = list(DNSDelegation.objects.filter(zone=zone).select_related("zone"))
        for delegation in delegations:
            cut_key = dns_name_key(delegation.get_fqdn())
            if owner_key != cut_key and not is_subdomain(owner_key, cut_key):
                continue
            if isinstance(record, NSRecord) and owner_key == cut_key:
                continue
            if record._meta.model_name in ("arecord", "aaaarecord") and owner_key in self._glue_owner_keys(delegations):
                continue
            raise ComplianceError(
                {
                    "name": (
                        f"This record is at or below the zone cut at {delegation.get_fqdn()}, so it is not "
                        f"authoritative data of zone {zone.name}. Move it to the delegated zone or remove it."
                    )
                }
            )

    @staticmethod
    def _glue_owner_keys(delegations):
        """Return the names of every name server of the given delegations, as `dns_name_key()` values."""
        return {
            dns_name_key(server)
            for delegation in delegations
            for server in delegation.ns_records.values_list("server", flat=True)
        }


def _record_not_occluded_rule(model_name, label):
    return type(
        f"{label}NotOccludedRule",
        (RecordNotOccludedRule,),
        {
            "__doc__": f"Report {label} records hidden below a zone cut.",
            "name": f"{label} Record Not Below a Zone Cut",
            "model": f"nautobot_dns_models.{model_name}",
        },
    )


custom_validators = [
    DNSDelegationNameServersRule,
    DNSDelegationGlueRule,
    DNSDelegationChildGlueRule,
    DNSDelegationChildNameServersRule,
    DNSZoneDelegatedRule,
    *(
        _record_not_occluded_rule(model_name, label)
        for model_name, label in (
            ("arecord", "A"),
            ("aaaarecord", "AAAA"),
            ("cnamerecord", "CNAME"),
            ("mxrecord", "MX"),
            ("nsrecord", "NS"),
            ("ptrrecord", "PTR"),
            ("srvrecord", "SRV"),
            ("txtrecord", "TXT"),
        )
    ),
]
