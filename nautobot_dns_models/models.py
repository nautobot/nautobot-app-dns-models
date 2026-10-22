"""Models for Nautobot DNS Models."""
# pylint: disable=too-many-lines

import dataclasses

from constance import config as constance_config
from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator, validate_email
from django.db import models
from django.db.models.functions import Lower
from django.db.models.signals import post_delete
from django.dispatch import receiver
from nautobot.apps.models import BaseModel, PrimaryModel, extras_features
from nautobot.core.models.fields import ForeignKeyWithAutoRelatedName
from nautobot.extras.models import StatusField
from nautobot.ipam.choices import IPAddressVersionChoices
from netutils.ip import ipaddress_address

from nautobot_dns_models.choices import DNSForwardingRuleActionChoices

# Reverse-DNS roots per RFC 1035 §3.5 and RFC 3596 §2.5
RESERVED_ROOTS = {"in-addr.arpa", "ip6.arpa", "arpa"}

# All DNS integer fields use the full unsigned 32-bit range (0..4294967295).
# RFC 8767 §4 defines TTL as a 32-bit unsigned integer (updating RFC 2181).
# RFC 1035 §3.3.13 defines SOA fields as 32-bit values, explicitly unsigned for SERIAL and MINIMUM;
# RFC 1982 §7 specifies SERIAL's uint32 range and arithmetic.
UINT32_MAX = 2**32 - 1


def dns_wire_label_length(label):
    """Return the wire-format (IDNA/Punycode) length of a DNS label."""
    if label.isascii():
        return len(label)

    return len("xn--" + label.encode("punycode").decode("ascii"))


def _find_unescaped_dot(value):
    """Return the position of the first unescaped dot, or None."""
    character_is_escaped = False
    for index, character in enumerate(value):
        if character_is_escaped:
            character_is_escaped = False
            continue

        if character == "\\":
            character_is_escaped = True
        elif character == ".":
            return index

    return None


def normalize_soa_rname(value):
    """Normalize a basic DNS-style SOA RNAME mailbox to email form."""
    if not value or "@" in value:
        return value

    value_without_root = value.removesuffix(".")
    separator = _find_unescaped_dot(value_without_root)
    if separator is None:
        return value_without_root

    local_part = value_without_root[:separator].replace(r"\.", ".")
    domain = value_without_root[separator + 1 :]
    if not local_part or not domain or "\\" in local_part or "\\" in domain or "" in domain.split("."):
        return value

    return f"{local_part}@{domain}"


def validate_dns_label(label, field="name"):
    """
    Validate a DNS label for wire-format length using punycode encoding.

    Only checks for non-empty and length.
    """
    if not label:
        raise ValidationError({field: "Empty labels are not allowed"})
    length = dns_wire_label_length(label)
    if length > 63:
        raise ValidationError(
            {field: f"Label '{label}' exceeds the maximum length of 63 bytes (octets) in wire format."}
        )
    return length


def normalize_dns_name(value):
    """Return `value` lowercased and without a trailing dot, for comparing DNS names."""
    return value.strip().rstrip(".").lower()


def is_same_or_subdomain(name, domain):
    """Return True if the normalized `name` equals the normalized `domain` or lies beneath it."""
    return name == domain or name.endswith(f".{domain}")


def record_fqdn(record_name, zone_name):
    """Return the normalized FQDN of a record owner name within a zone.

    An empty name or `@` is the zone apex. A name that already ends with the zone name is treated as
    zone-qualified, matching the trailing-dot normalization in `DNSRecord.clean()`. Any other name is
    relative to the zone.
    """
    zone_fqdn = normalize_dns_name(zone_name)
    name = normalize_dns_name(record_name)
    if name in ("", "@"):
        return zone_fqdn
    if is_same_or_subdomain(name, zone_fqdn):
        return name
    return f"{name}.{zone_fqdn}"


def prior_checks_ptr_record_creation(record):
    """Check if there is a matching reverse zone for this A/AAAA record's PTR record before creating it.

    Called from clean() so the failure surfaces before any DB write.
    """
    ptrdname = ipaddress_address(record.ip_address.host, "reverse_pointer")
    if DNSZone.find_reverse_zone_for_ptrdname(ptrdname, dns_view=record.zone.dns_view) is None:
        raise ValidationError(
            {
                "ip_address": (
                    f"Cannot auto-create PTR record: no matching reverse zone found "
                    f"in view '{record.zone.dns_view}' for {record.ip_address}."
                )
            }
        )


def create_auto_ptr_record(record):
    """Create a PTR record for the given A/AAAA record's IP address.

    Raises ValidationError if no matching reverse zone is found in the same DNS view.
    Skips creation silently if a PTR with the same owner name already exists in that reverse zone.
    """
    ptr_name = ipaddress_address(record.ip_address.host, "reverse_pointer")
    reverse_zone = DNSZone.find_reverse_zone_for_ptrdname(ptr_name, dns_view=record.zone.dns_view)
    if reverse_zone is None:
        raise ValidationError(
            {
                "ip_address": (
                    f"Cannot auto-create PTR record: no matching reverse zone found "
                    f"in view '{record.zone.dns_view}' for {record.ip_address}."
                )
            }
        )
    # RFC 1035 §3.5: PTR owner name is the reverse pointer, which is relative to the reverse zone.
    # As an example name is 20 and the whole fqdn `20.1.168.192.in-addr.arpa`
    relative_name = ptr_name.removesuffix(f".{reverse_zone.name}")
    # RFC 1035 §3.3.12: PTR RDATA (PTRDNAME) is the FQDN of the forward name.
    # Creating a PTR record for A record www in example.com, this should be `www.example.com`
    forward_fqdn = f"{record.name}.{record.zone.name}"
    if PTRRecord.objects.filter(name=relative_name, zone=reverse_zone).exists():
        return

    PTRRecord(name=relative_name, ptrdname=forward_fqdn, zone=reverse_zone).validated_save()


class DNSModel(PrimaryModel):
    """Abstract Model for Nautobot DNS Models."""

    #
    # name is effectively a NOOP here; it's overridden in both subclasses but
    # is here so that linters don't complain about it being used in clean().
    name = models.CharField(max_length=200)
    ttl = models.PositiveBigIntegerField(
        validators=[MaxValueValidator(UINT32_MAX)], default=3600, help_text="Time To Live."
    )
    enabled = models.BooleanField(
        default=True,
        help_text="Whether this object is eligible for publication by external integrations.",
    )

    class Meta:
        """Meta class."""

        abstract = True

    def __str__(self):
        """Stringify instance."""
        return self.name  # pylint: disable=no-member

    _validate_dns_label = staticmethod(validate_dns_label)

    def clean(self):
        """
        Validate DNS label length and format per RFC 1035 §3.1 using punycode for wire-format length.

        Ensures each label in the name is ≤ 63 bytes (octets) in wire format and not empty.
        """
        super().clean()

        validation_level = getattr(constance_config, "nautobot_dns_models__DNS_VALIDATION_LEVEL")
        if validation_level == "wire-format":
            # Allow apex (empty) names; otherwise validate each non-empty label.
            if self.name != "":
                label_list = self.name.split(".")
                for label in label_list:
                    self._validate_dns_label(label, field="name")


@extras_features(
    "custom_fields",
    "custom_links",
    "custom_validators",
    "export_templates",
    "graphql",
    "relationships",
    "webhooks",
)
class DNSView(PrimaryModel):
    """Model for DNS Views."""

    name = models.CharField(max_length=200, help_text="Name of the View.", unique=True)
    description = models.TextField(help_text="Description of the View.", blank=True)
    prefixes = models.ManyToManyField(
        to="ipam.Prefix",
        related_name="dns_views",
        through="DNSViewPrefixAssignment",
        through_fields=("dns_view", "prefix"),
        blank=True,
        help_text="IP Prefixes that define the View.",
    )

    class Meta:
        """Meta attributes for DNSView."""

        verbose_name = "DNS View"
        verbose_name_plural = "DNS Views"

    def __str__(self):
        """Stringify instance."""
        return self.name


@extras_features(
    "custom_fields",
    "custom_links",
    "custom_validators",
    "export_templates",
    "graphql",
    "relationships",
    "webhooks",
)
class DNSRegistrar(PrimaryModel):
    """Model for DNS Registrars."""

    name = models.CharField(max_length=200, help_text="Name of the Registrar.", unique=True)
    url = models.URLField(max_length=500, blank=True, help_text="Registrar URL.")
    account_number = models.CharField(max_length=100, blank=True, help_text="Registrar account number.")

    class Meta:
        """Meta attributes for DNSRegistrar."""

        verbose_name = "DNS Registrar"
        verbose_name_plural = "DNS Registrars"

    def __str__(self):
        """Stringify instance."""
        return self.name


def get_default_view_pk():
    """Return the default DNSView ID, creating it if necessary."""
    default_view, _ = DNSView.objects.get_or_create(
        name="Default", defaults={"description": "Default DNS view. Created by Nautobot DNS Models app."}
    )
    return default_view.pk


@dataclasses.dataclass
class ZoneDelegation:
    """A delegation point in a parent zone, derived from the NS records at that name.

    This is not stored in the database. See `DNSZone.get_delegations()`.
    """

    zone: "DNSZone"
    fqdn: str
    ns_records: list = dataclasses.field(default_factory=list)
    glue_records: list = dataclasses.field(default_factory=list)
    child_zone: "DNSZone | None" = None

    @property
    def servers(self):
        """Sorted, normalized FQDNs of the name servers the delegation points to."""
        return sorted({normalize_dns_name(ns_record.server) for ns_record in self.ns_records})

    @property
    def glue_required_servers(self):
        """Name servers at or below the delegated name, which resolvers can only reach through glue."""
        return [server for server in self.servers if is_same_or_subdomain(server, self.fqdn)]

    @property
    def missing_glue_servers(self):
        """Name servers that need glue but have no A/AAAA record in the parent zone."""
        glue_fqdns = {record_fqdn(record.name, self.zone.name) for record in self.glue_records}
        return [server for server in self.glue_required_servers if server not in glue_fqdns]


@extras_features(
    "custom_fields",
    "custom_links",
    "custom_validators",
    "export_templates",
    "graphql",
    "relationships",
    "webhooks",
)
class DNSZone(DNSModel):
    """Model for DNS SOA Records. An SOA Record defines a DNS Zone."""

    name = models.CharField(max_length=200, help_text="FQDN of the Zone, w/ TLD. e.g example.com")
    dns_view = ForeignKeyWithAutoRelatedName(
        DNSView,
        on_delete=models.PROTECT,
        help_text="The DNS View this Zone belongs to.",
        verbose_name="View",
        default=get_default_view_pk,
    )
    ttl = models.PositiveBigIntegerField(
        validators=[MaxValueValidator(UINT32_MAX)],
        default=3600,
        help_text="Time To Live.",
        verbose_name="TTL",
    )
    filename = models.CharField(max_length=200, help_text="Filename of the Zone File.")
    description = models.TextField(help_text="Description of the Zone.", blank=True)
    soa_mname = models.CharField(
        max_length=200,
        help_text="FQDN of the Authoritative Name Server for Zone.",
        null=False,
        verbose_name="SOA MNAME",
    )
    soa_rname = models.CharField(
        max_length=254,
        help_text="Mailbox of the person responsible for the zone or a single-label placeholder.",
        verbose_name="SOA RNAME",
    )
    soa_refresh = models.PositiveBigIntegerField(
        validators=[MaxValueValidator(UINT32_MAX)],
        default=86400,
        help_text="Number of seconds after which secondary name servers should query the master for the SOA record, to detect zone changes.",
        verbose_name="SOA Refresh",
    )
    soa_retry = models.PositiveBigIntegerField(
        validators=[MaxValueValidator(UINT32_MAX)],
        default=7200,
        help_text="Number of seconds after which secondary name servers should retry to request the serial number from the master if the master does not respond.",
        verbose_name="SOA Retry",
    )
    soa_expire = models.PositiveBigIntegerField(
        validators=[MaxValueValidator(UINT32_MAX)],
        default=3600000,
        help_text="Number of seconds after which secondary name servers should stop answering request for this zone if the master does not respond. This value must be bigger than the sum of Refresh and Retry.",
        verbose_name="SOA Expire",
    )
    soa_serial = models.PositiveBigIntegerField(
        validators=[MaxValueValidator(UINT32_MAX)],
        default=0,
        help_text="Serial number of the zone. This value must be incremented each time the zone is changed, and secondary DNS servers must be able to retrieve this value to check if the zone has been updated.",
        verbose_name="SOA Serial",
    )
    soa_minimum = models.PositiveBigIntegerField(
        validators=[MaxValueValidator(UINT32_MAX)],
        default=3600,
        help_text="Minimum TTL for records in this zone.",
        verbose_name="SOA Minimum",
    )

    tenant = models.ForeignKey(
        to="tenancy.Tenant",
        on_delete=models.PROTECT,
        related_name="dns_zones",
        blank=True,
        null=True,
    )
    auto_create_ptr = models.BooleanField(
        default=False,
        help_text="Automatically create PTR records when A/AAAA records are created in this zone.",
        verbose_name="Auto-create PTR Records",
    )
    # Children are moved up to the next ancestor when their parent is deleted (see refresh_orphaned_child_zones),
    # so SET_NULL only covers the moment between the delete and that update.
    parent_zone = models.ForeignKey(
        to="self",
        on_delete=models.SET_NULL,
        related_name="child_zones",
        blank=True,
        null=True,
        editable=False,
        help_text="Nearest ancestor zone in the same DNS View. Set automatically.",
        verbose_name="Parent Zone",
    )

    class Meta:
        """Meta attributes for DNSZone."""

        unique_together = [["name", "dns_view"]]
        verbose_name = "DNS Zone"
        verbose_name_plural = "DNS Zones"

    def __str__(self):
        """Stringify instance."""
        return f"{self.name} ({self.dns_view})"

    def clean(self):
        """Normalize plain DNS-style RNAME mailboxes to email form and reject names used by forwarding rules."""
        super().clean()

        if (
            self.dns_view_id
            and DNSForwardingRule.objects.annotate(name_lower=Lower("name"))
            .filter(dns_view_id=self.dns_view_id, name_lower=normalize_dns_name(self.name))
            .exists()
        ):
            raise ValidationError(
                {"name": "A DNS forwarding rule with this name already exists in this view. Remove it first."}
            )

        invalid_rname_message = (
            "SOA RNAME must be a valid email address, a basic DNS-style mailbox with a fully qualified domain, "
            "or a single-label placeholder."
        )
        normalized_soa_rname = normalize_soa_rname(self.soa_rname)
        if "@" in normalized_soa_rname:
            try:
                validate_email(normalized_soa_rname)
            except ValidationError as exc:
                raise ValidationError({"soa_rname": invalid_rname_message}) from exc
        else:
            if not normalized_soa_rname or "." in normalized_soa_rname or "\\" in normalized_soa_rname:
                raise ValidationError({"soa_rname": invalid_rname_message})
            self._validate_dns_label(normalized_soa_rname, field="soa_rname")

        # Keep the in-memory instance canonical for callers of clean() or full_clean()
        # that do not immediately save it.
        self.soa_rname = normalized_soa_rname

    def save(self, *args, **kwargs):
        """Normalize the RNAME and keep `parent_zone` up to date for this zone and its relatives."""
        self.soa_rname = normalize_soa_rname(self.soa_rname)
        previous = None
        if self.present_in_database:
            previous = DNSZone.objects.filter(pk=self.pk).values("name", "dns_view_id").first()
        self.parent_zone = self.find_enclosing_zone(self.name, self.dns_view_id, exclude_pk=self.pk)
        super().save(*args, **kwargs)
        if previous != {"name": self.name, "dns_view_id": self.dns_view_id}:
            self._refresh_related_parent_zones()

    def update_parent_zone(self):
        """Recompute and store `parent_zone` without a full save, so relatives can be updated in bulk."""
        parent = self.find_enclosing_zone(self.name, self.dns_view_id, exclude_pk=self.pk)
        parent_pk = parent.pk if parent else None
        if parent_pk != self.parent_zone_id:
            DNSZone.objects.filter(pk=self.pk).update(parent_zone=parent)
            self.parent_zone = parent

    def _refresh_related_parent_zones(self):
        """Update zones whose nearest ancestor may have changed because this zone was created, renamed or moved."""
        affected = DNSZone.objects.filter(
            models.Q(parent_zone=self)
            | models.Q(dns_view_id=self.dns_view_id, name__iendswith=f".{normalize_dns_name(self.name)}")
        ).exclude(pk=self.pk)
        for zone in affected:
            zone.update_parent_zone()

    @classmethod
    def find_enclosing_zone(cls, name, dns_view_id, exclude_pk=None):
        """Return the zone in the given view with the longest name that is a proper ancestor of `name`, or None."""
        labels = normalize_dns_name(name).split(".")
        ancestor_names = [".".join(labels[i:]) for i in range(1, len(labels))]
        if not ancestor_names or dns_view_id is None:
            return None
        zones = cls.objects.annotate(name_lower=Lower("name")).filter(
            dns_view_id=dns_view_id, name_lower__in=ancestor_names
        )
        if exclude_pk is not None:
            zones = zones.exclude(pk=exclude_pk)
        return max(zones, key=lambda zone: len(zone.name_lower), default=None)

    @classmethod
    def get_apex_ns_servers_by_zone(cls, zones):
        """Return `{zone pk: sorted, normalized apex name servers}` for the given zones, using one query."""
        zone_names = {zone.pk: zone.name for zone in zones}
        servers = {pk: set() for pk in zone_names}
        for ns_record in NSRecord.objects.filter(zone__in=list(zone_names)):
            zone_name = zone_names[ns_record.zone_id]
            if record_fqdn(ns_record.name, zone_name) == normalize_dns_name(zone_name):
                servers[ns_record.zone_id].add(normalize_dns_name(ns_record.server))
        return {pk: sorted(zone_servers) for pk, zone_servers in servers.items()}

    def get_apex_ns_servers(self):
        """Return the sorted, normalized name servers of the NS records at this zone's apex."""
        return self.get_apex_ns_servers_by_zone([self])[self.pk]

    def get_delegations(self):
        """Return the delegations in this zone, derived from the NS records below the apex.

        NS records below another delegation point are hidden by it, so they do not form a delegation of their own
        (see `get_occluded_records()`).

        Returns:
            (list[ZoneDelegation]): One entry per delegated name, ordered by FQDN.
        """
        zone_fqdn = normalize_dns_name(self.name)
        by_fqdn = {}
        for ns_record in NSRecord.objects.filter(zone=self):
            fqdn = record_fqdn(ns_record.name, self.name)
            if fqdn != zone_fqdn:
                by_fqdn.setdefault(fqdn, ZoneDelegation(zone=self, fqdn=fqdn)).ns_records.append(ns_record)

        delegations = {
            fqdn: delegation
            for fqdn, delegation in by_fqdn.items()
            if not any(other != fqdn and is_same_or_subdomain(fqdn, other) for other in by_fqdn)
        }
        if not delegations:
            return []

        child_zones = (
            DNSZone.objects.annotate(name_lower=Lower("name"))
            .filter(dns_view_id=self.dns_view_id, name_lower__in=list(delegations))
            .select_related("dns_view")
        )
        for child_zone in child_zones:
            delegations[child_zone.name_lower].child_zone = child_zone

        address_records = [
            *ARecord.objects.filter(zone=self).select_related("ip_address"),
            *AAAARecord.objects.filter(zone=self).select_related("ip_address"),
        ]
        for delegation in delegations.values():
            glue_names = set(delegation.glue_required_servers)
            delegation.glue_records = [
                record for record in address_records if record_fqdn(record.name, self.name) in glue_names
            ]

        return [delegations[fqdn] for fqdn in sorted(delegations)]

    def get_parent_delegation(self):
        """Return the delegation of this zone in its parent zone, or None if the parent has no NS records for it."""
        if self.parent_zone is None:
            return None
        zone_fqdn = normalize_dns_name(self.name)
        return next(
            (delegation for delegation in self.parent_zone.get_delegations() if delegation.fqdn == zone_fqdn),
            None,
        )

    def get_occluded_records(self, delegations=None):
        """Return the records in this zone that a delegation point hides.

        Resolvers do not receive data at or below a zone cut from the parent zone, except the NS records that form
        the cut and A/AAAA glue for the delegations' name servers.

        Args:
            delegations (list[ZoneDelegation], optional): Result of `get_delegations()`, if already computed.
        """
        if delegations is None:
            delegations = self.get_delegations()
        if not delegations:
            return []

        cuts = [delegation.fqdn for delegation in delegations]
        glue_names = {server for delegation in delegations for server in delegation.servers}
        # Only fetch names at or below a cut, written either relative to the zone or zone-qualified.
        zone_fqdn = normalize_dns_name(self.name)
        below_cuts = models.Q()
        for cut in cuts:
            for name in (cut.removesuffix(f".{zone_fqdn}"), cut):
                below_cuts |= models.Q(name__iexact=name) | models.Q(name__iendswith=f".{name}")
        record_models = (NSRecord, ARecord, AAAARecord, CNAMERecord, MXRecord, TXTRecord, PTRRecord, SRVRecord)
        occluded = []
        for record_model in record_models:
            for record in record_model.objects.filter(below_cuts, zone=self):
                fqdn = record_fqdn(record.name, self.name)
                cut = next((cut for cut in cuts if is_same_or_subdomain(fqdn, cut)), None)
                if cut is None:
                    continue
                if isinstance(record, NSRecord) and fqdn == cut:
                    continue
                if isinstance(record, (ARecord, AAAARecord)) and fqdn in glue_names:
                    continue
                occluded.append(record)
        return occluded

    def get_delegation_warnings(self, delegations=None, parent_delegations=None):
        """Return consistency problems with the delegations this zone makes and the delegation it receives.

        Args:
            delegations (list[ZoneDelegation], optional): Result of `get_delegations()`, if already computed.
            parent_delegations (list[ZoneDelegation], optional): Result of `parent_zone.get_delegations()`,
                if already computed.

        Returns:
            (list[str]): Human-readable warnings. None of them block saving.
        """
        if delegations is None:
            delegations = self.get_delegations()
        warnings = self._outgoing_delegation_warnings(delegations)
        if self.parent_zone is not None:
            if parent_delegations is None:
                parent_delegations = self.parent_zone.get_delegations()
            warnings.extend(self._incoming_delegation_warnings(parent_delegations))
        return warnings

    def _outgoing_delegation_warnings(self, delegations):
        """Return problems with the delegations this zone makes to its children."""
        warnings = []
        child_apex_servers = self.get_apex_ns_servers_by_zone(
            [delegation.child_zone for delegation in delegations if delegation.child_zone is not None]
        )

        for delegation in delegations:
            for server in delegation.missing_glue_servers:
                warnings.append(
                    f"Delegation {delegation.fqdn}: name server {server} is inside the delegated name "
                    "but has no A/AAAA glue record in this zone."
                )
            if delegation.child_zone is not None:
                child_servers = child_apex_servers[delegation.child_zone.pk]
                if child_servers != delegation.servers:
                    warnings.append(
                        f"Delegation {delegation.fqdn}: the NS records here ({', '.join(delegation.servers)}) "
                        f"do not match the apex NS records of zone {delegation.child_zone.name} "
                        f"({', '.join(child_servers) or 'none'})."
                    )

        # A child zone below another delegated name is delegated from that zone, which Nautobot does not model.
        cuts = [delegation.fqdn for delegation in delegations]
        for child_zone in self.child_zones.all():
            if not any(is_same_or_subdomain(normalize_dns_name(child_zone.name), cut) for cut in cuts):
                warnings.append(f"Child zone {child_zone.name} has no NS records in this zone, so it is not delegated.")

        occluded = self.get_occluded_records(delegations)
        if occluded:
            names = sorted({record_fqdn(record.name, self.name) for record in occluded})
            warnings.append(
                f"{len(occluded)} record(s) at or below a delegation point are hidden by it: {', '.join(names)}."
            )
        return warnings

    def _incoming_delegation_warnings(self, parent_delegations):
        """Return problems with how the parent zone delegates this zone."""
        zone_fqdn = normalize_dns_name(self.name)
        parent_delegation = next((d for d in parent_delegations if d.fqdn == zone_fqdn), None)
        if parent_delegation is None:
            if any(is_same_or_subdomain(zone_fqdn, d.fqdn) for d in parent_delegations):
                return []
            return [f"Parent zone {self.parent_zone.name} has no NS records for this zone, so it is not delegated."]

        apex_servers = self.get_apex_ns_servers()
        if parent_delegation.servers == apex_servers:
            return []
        return [
            f"The NS records for this zone in parent zone {self.parent_zone.name} "
            f"({', '.join(parent_delegation.servers)}) do not match this zone's apex NS records "
            f"({', '.join(apex_servers) or 'none'})."
        ]

    @classmethod
    def find_reverse_zone_for_ptrdname(cls, ptrdname, dns_view=None):
        """Return the most-specific reverse DNSZone whose name matches a tail of `ptrdname`, otherwise None."""
        labels = ptrdname.split(".")
        for i in range(1, len(labels)):
            zone_name = ".".join(labels[i:])
            # We shouldn't match those cause are reserved to IANA
            if zone_name in RESERVED_ROOTS:
                break

            zones = cls.objects.filter(name=zone_name)
            if dns_view is not None:
                zones = zones.filter(dns_view=dns_view)
            zone = zones.first()
            if zone:
                return zone
        return None


@receiver(post_delete, sender=DNSZone)
def refresh_orphaned_child_zones(sender, instance, **kwargs):  # pylint: disable=unused-argument
    """Move the children of a deleted zone up to their nearest remaining ancestor.

    A receiver, unlike an overridden `delete()`, also runs for queryset deletes such as UI bulk delete.
    By the time it runs, `on_delete=SET_NULL` has already cleared the children's `parent_zone`.
    """
    orphans = DNSZone.objects.filter(
        dns_view_id=instance.dns_view_id,
        parent_zone__isnull=True,
        name__iendswith=f".{normalize_dns_name(instance.name)}",
    )
    for zone in orphans:
        zone.update_parent_zone()


@extras_features(
    "custom_fields",
    "custom_links",
    "custom_validators",
    "export_templates",
    "graphql",
    "relationships",
    "statuses",
    "webhooks",
)
class DNSRegistration(PrimaryModel):
    """Model representing the registration of a DNS zone with a registrar."""

    dns_registrar = ForeignKeyWithAutoRelatedName(
        DNSRegistrar,
        on_delete=models.PROTECT,
        help_text="Registrar used for this zone registration.",
        verbose_name="Registrar",
    )
    dns_zone = ForeignKeyWithAutoRelatedName(
        DNSZone,
        on_delete=models.PROTECT,
        help_text="Zone that is registered.",
        verbose_name="Zone",
    )
    status = StatusField(
        null=False,
        on_delete=models.PROTECT,
        help_text="Status of the DNS registration.",
        to="extras.status",
    )
    expiration_date = models.DateField(null=True, blank=True, help_text="Domain expiration date.")
    auto_renewal = models.BooleanField(default=False, help_text="Whether auto renewal is enabled.")
    registry_locked = models.BooleanField(default=False, help_text="Whether registry lock is enabled.")
    transfer_locked = models.BooleanField(default=False, help_text="Whether transfer lock is enabled.")
    privacy_enabled = models.BooleanField(default=False, help_text="Whether privacy protection is enabled.")
    website_forwarding_enabled = models.BooleanField(default=False, help_text="Whether website forwarding is enabled.")
    renewal_term_months = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(1200)],
        help_text="Renewal term in months.",
    )
    dnssec_enabled = models.BooleanField(
        default=False, help_text="Whether DNSSEC is enabled.", verbose_name="DNSSEC Enabled"
    )

    class Meta:
        """Meta attributes for DNSRegistration."""

        unique_together = [["dns_registrar", "dns_zone"]]
        verbose_name = "DNS Registration"
        verbose_name_plural = "DNS Registrations"

    def __str__(self):
        """Stringify instance."""
        return f"{self.dns_zone} @ {self.dns_registrar}"


@extras_features("graphql")
class DNSViewPrefixAssignment(BaseModel):
    """Through model for DNSView and Prefix many-to-many relationship."""

    dns_view = ForeignKeyWithAutoRelatedName(
        DNSView,
        on_delete=models.CASCADE,
    )
    prefix = ForeignKeyWithAutoRelatedName(to="ipam.Prefix", on_delete=models.CASCADE)

    class Meta:
        """Meta attributes for DNSViewPrefixAssignment."""

        unique_together = [["dns_view", "prefix"]]
        verbose_name = "DNS View Prefix Assignment"
        verbose_name_plural = "DNS View Prefix Assignments"

    def __str__(self):
        """Stringify instance."""
        return f"{self.dns_view}: {self.prefix}"


class DNSRecord(DNSModel):
    """Primary Dns Record model for plugin."""

    name = models.CharField(max_length=200, help_text="FQDN of the Record, w/o TLD.")
    zone = ForeignKeyWithAutoRelatedName(DNSZone, on_delete=models.PROTECT)
    _ttl = models.PositiveBigIntegerField(
        validators=[MaxValueValidator(UINT32_MAX)],
        help_text="Time To Live (if no value is given, the Zone TTL will be used).",
        blank=True,
        null=True,
        verbose_name="TTL",
    )
    description = models.TextField(help_text="Description of the Record.", blank=True)
    comment = models.CharField(max_length=200, help_text="Comment for the Record.", blank=True)

    def clean(self):
        """
        Extend base validation to check total DNS name wire format length per RFC 1035 §3.1 using punycode for wire-format length.

        In addition to label checks, ensures the full DNS name (record + zone) does not exceed 255 bytes (octets) in wire format.
        """
        # Normalize trailing-dot only when the record name is zone-qualified (e.g., "host.example.com.")
        if (
            isinstance(self.name, str)
            and self.name.endswith(".")
            and getattr(self, "zone", None)
            and getattr(self.zone, "name", None)
            and self.name.endswith(f"{self.zone.name}.")
        ):
            self.name = self.name[:-1]

        super().clean()

        if not hasattr(self, "zone"):
            raise ValidationError({"zone": "Zone is required"})

        self._validate_total_wire_length_if_enabled()
        self._enforce_cname_exclusivity_if_enabled()

    def _validate_total_wire_length_if_enabled(self) -> None:
        """Validate full DNS name (record + zone) total wire-format length if wire-format validation is enabled."""
        validation_level = getattr(constance_config, "nautobot_dns_models__DNS_VALIDATION_LEVEL")
        if validation_level != "wire-format":
            return

        record_label_list = [] if self.name == "" else self.name.split(".")
        zone_label_list = self.zone.name.split(".")

        wire_length = 0
        for label in record_label_list:
            wire_length += 1 + dns_wire_label_length(label)
        for label in zone_label_list:
            wire_length += 1 + dns_wire_label_length(label)
        wire_length += 1  # Final zero-length root label

        if wire_length > 255:
            raise ValidationError({"name": "Total length of DNS name cannot exceed 255 bytes (octets) in wire format."})

    def _enforce_cname_exclusivity_if_enabled(self) -> None:
        """Enforce mutual exclusivity between CNAME and other record types for exact (name, zone) matches."""
        enforce = getattr(constance_config, "nautobot_dns_models__CNAME_RESTRICTION_ENABLED", True)
        if not enforce or getattr(self, "name", None) is None or getattr(self, "zone_id", None) is None:
            return

        if isinstance(self, CNAMERecord):
            conflicting_models = (NSRecord, ARecord, AAAARecord, MXRecord, TXTRecord, PTRRecord, SRVRecord)
            for model in conflicting_models:
                if model.objects.filter(name=self.name, zone_id=self.zone_id).exists():
                    raise ValidationError(
                        {"name": "CNAME cannot co-exist with other records of the same name in this zone."}
                    )
        else:
            if CNAMERecord.objects.filter(name=self.name, zone_id=self.zone_id).exists():
                raise ValidationError({"name": "Record cannot co-exist with a CNAME of the same name in this zone."})

    class Meta:
        """Meta attributes for DnsRecord."""

        abstract = True

    @property
    def ttl(self):
        """Return the TTL value for the record."""
        if self._ttl is None:
            return self.zone.ttl  # pylint: disable=no-member
        return self._ttl

    @ttl.setter
    def ttl(self, value):
        """Set the TTL value for the record."""
        self._ttl = value


@extras_features(
    "custom_fields",
    "custom_links",
    "custom_validators",
    "export_templates",
    "relationships",
    "webhooks",
)
class NSRecord(DNSRecord):
    """NS Record model."""

    server = models.CharField(max_length=200, help_text="FQDN of an authoritative Name Server.")

    class Meta:
        """Meta attributes for NSRecord."""

        unique_together = [["name", "server", "zone"]]
        verbose_name = "NS Record"
        verbose_name_plural = "NS Records"


@extras_features(
    "custom_fields",
    "custom_links",
    "custom_validators",
    "export_templates",
    "relationships",
    "webhooks",
)
class ARecord(DNSRecord):
    """A Record model."""

    ip_address = models.ForeignKey(
        to="ipam.IPAddress",
        on_delete=models.CASCADE,
        limit_choices_to={"ip_version": IPAddressVersionChoices.VERSION_4},
        help_text="IP address for the record.",
        verbose_name="IP Address",
    )

    class Meta:
        """Meta attributes for ARecord."""

        unique_together = [["name", "ip_address", "zone"]]
        verbose_name = "A Record"
        verbose_name_plural = "A Records"

    def clean(self):
        """Validate that the referenced IP address is IPv4.

        Guard against dereferencing the relation when it's unset to avoid
        RelatedObjectDoesNotExist during form/model validation.
        """
        super().clean()
        if self.ip_address_id is None:
            return
        if self.ip_address.ip_version != IPAddressVersionChoices.VERSION_4:
            raise ValidationError({"ip_address": "ARecord must reference an IPv4 address."})
        if self._state.adding and self.zone.auto_create_ptr:  # pylint: disable=no-member
            prior_checks_ptr_record_creation(self)

    def save(self, *args, **kwargs):
        """Validate, save, and auto-create a PTR if the forward zone has auto_create_ptr enabled."""
        is_new = self._state.adding
        self.clean()
        super().save(*args, **kwargs)
        if is_new and self.zone.auto_create_ptr:  # pylint: disable=no-member
            create_auto_ptr_record(self)


@extras_features(
    "custom_fields",
    "custom_links",
    "custom_validators",
    "export_templates",
    "relationships",
    "webhooks",
)
class AAAARecord(DNSRecord):
    """AAAA Record model."""

    ip_address = models.ForeignKey(
        to="ipam.IPAddress",
        on_delete=models.CASCADE,
        limit_choices_to={"ip_version": IPAddressVersionChoices.VERSION_6},
        help_text="IP address for the record.",
        verbose_name="IP Address",
    )

    class Meta:
        """Meta attributes for AAAARecord."""

        unique_together = [["name", "ip_address", "zone"]]
        verbose_name = "AAAA Record"
        verbose_name_plural = "AAAA Records"

    def clean(self):
        """Validate that the referenced IP address is IPv6.

        Guard against dereferencing the relation when it's unset to avoid
        RelatedObjectDoesNotExist during form/model validation.
        """
        super().clean()
        if self.ip_address_id is None:
            return
        if self.ip_address.ip_version != IPAddressVersionChoices.VERSION_6:
            raise ValidationError({"ip_address": "AAAARecord must reference an IPv6 address."})
        if self._state.adding and self.zone.auto_create_ptr:  # pylint: disable=no-member
            prior_checks_ptr_record_creation(self)

    def save(self, *args, **kwargs):
        """Validate, save, and auto-create a PTR if the forward zone has auto_create_ptr enabled."""
        is_new = self._state.adding
        self.clean()
        super().save(*args, **kwargs)
        if is_new and self.zone.auto_create_ptr:  # pylint: disable=no-member
            create_auto_ptr_record(self)


@extras_features(
    "custom_fields",
    "custom_links",
    "custom_validators",
    "export_templates",
    "relationships",
    "webhooks",
)
class CNAMERecord(DNSRecord):
    """CNAME Record model."""

    alias = models.CharField(max_length=200, help_text="FQDN of the Alias.")

    class Meta:
        """Meta attributes for CNAMERecord."""

        unique_together = [["name", "alias", "zone"]]
        verbose_name = "CNAME Record"
        verbose_name_plural = "CNAME Records"


@extras_features(
    "custom_fields",
    "custom_links",
    "custom_validators",
    "export_templates",
    "relationships",
    "webhooks",
)
class MXRecord(DNSRecord):
    """MX Record model."""

    preference = models.IntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(65535)],
        default=10,
        help_text="Preference for the MX Record.",
    )
    mail_server = models.CharField(max_length=200, help_text="FQDN of the Mail Server.")

    class Meta:
        """Meta attributes for MXRecord."""

        unique_together = [["name", "mail_server", "zone"]]
        verbose_name = "MX Record"
        verbose_name_plural = "MX Records"


@extras_features(
    "custom_fields",
    "custom_links",
    "custom_validators",
    "export_templates",
    "relationships",
    "webhooks",
)
class TXTRecord(DNSRecord):
    """TXT Record model."""

    text = models.CharField(max_length=256, help_text="Text for the TXT Record.")

    class Meta:
        """Meta attributes for TXTRecord."""

        unique_together = [["name", "text", "zone"]]
        verbose_name = "TXT Record"
        verbose_name_plural = "TXT Records"


@extras_features(
    "custom_fields",
    "custom_links",
    "custom_validators",
    "export_templates",
    "relationships",
    "webhooks",
)
class PTRRecord(DNSRecord):
    """PTR Record model."""

    ptrdname = models.CharField(
        max_length=200, help_text="A domain name that points to some location in the domain name space."
    )

    class Meta:
        """Meta attributes for PTRRecord."""

        unique_together = [["name", "ptrdname", "zone"]]
        verbose_name = "PTR Record"
        verbose_name_plural = "PTR Records"

    def __str__(self):
        """String representation of PTRRecord."""
        return self.ptrdname


@extras_features(
    "custom_fields",
    "custom_links",
    "custom_validators",
    "export_templates",
    "relationships",
    "webhooks",
)
class SRVRecord(DNSRecord):
    """SRV Record model."""

    priority = models.IntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(65535)],
        default=0,
        help_text="Priority of the SRV record.",
    )
    weight = models.IntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(65535)],
        default=0,
        help_text="Weight of the SRV record.",
    )
    port = models.IntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(65535)],
        help_text="Port number of the service.",
    )
    target = models.CharField(
        max_length=200,
        help_text="FQDN of the target host providing the service.",
    )

    class Meta:
        """Meta attributes for SRVRecord."""

        unique_together = [["name", "target", "port", "zone"]]
        verbose_name = "SRV Record"
        verbose_name_plural = "SRV Records"


@extras_features(
    "custom_fields",
    "custom_links",
    "custom_validators",
    "export_templates",
    "graphql",
    "relationships",
    "webhooks",
)
class DNSForwardingRule(PrimaryModel):
    """Model for DNS forwarding rules: how resolvers in a DNS View handle queries for a domain."""

    name = models.CharField(
        max_length=200,
        help_text="Domain the rule applies to, e.g. corp.example.com. Use a single dot (.) for global forwarders.",
    )
    dns_view = ForeignKeyWithAutoRelatedName(
        DNSView,
        on_delete=models.PROTECT,
        help_text="The DNS View this rule applies in.",
        verbose_name="View",
        default=get_default_view_pk,
    )
    action = models.CharField(
        max_length=50,
        choices=DNSForwardingRuleActionChoices,
        default=DNSForwardingRuleActionChoices.ACTION_FORWARD_FIRST,
        help_text=(
            "Forward first falls back to normal resolution when the forwarders fail, Forward only does not, "
            "and Do not forward exempts the domain from a broader rule."
        ),
    )
    forwarders = models.ManyToManyField(
        to="ipam.IPAddress",
        through="DNSForwardingRuleIPAddressAssignment",
        through_fields=("forwarding_rule", "ip_address"),
        related_name="dns_forwarding_rules",
        blank=True,
        editable=False,
        help_text="IP addresses of the servers queries are forwarded to.",
    )
    enabled = models.BooleanField(
        default=True,
        help_text="Whether this object is eligible for publication by external integrations.",
    )
    description = models.TextField(help_text="Description of the rule.", blank=True)
    tenant = models.ForeignKey(
        to="tenancy.Tenant",
        on_delete=models.PROTECT,
        related_name="dns_forwarding_rules",
        blank=True,
        null=True,
    )

    class Meta:
        """Meta attributes for DNSForwardingRule."""

        ordering = ["dns_view__name", "name"]
        unique_together = [["name", "dns_view"]]
        verbose_name = "DNS Forwarding Rule"
        verbose_name_plural = "DNS Forwarding Rules"

    def __str__(self):
        """Stringify instance."""
        return f"{self.name} ({self.dns_view})"

    @property
    def is_global(self):
        """Whether this rule holds the global forwarders, which apply to every name."""
        return self.name == "."

    def get_action_class(self):
        """Return the CSS class used to render the action in tables."""
        return DNSForwardingRuleActionChoices.CSS_CLASSES.get(self.action)

    def clean(self):
        """Validate the domain name and keep the rule consistent with zones and forwarders in the same view."""
        super().clean()

        validation_level = getattr(constance_config, "nautobot_dns_models__DNS_VALIDATION_LEVEL")
        if validation_level == "wire-format" and not self.is_global:
            for label in self.name.split("."):
                validate_dns_label(label, field="name")

        if self.dns_view_id:
            # unique_together is case-sensitive on PostgreSQL but not on MySQL, so check case-insensitively here.
            same_name = {"dns_view_id": self.dns_view_id, "name_lower": normalize_dns_name(self.name)}
            if (
                DNSForwardingRule.objects.annotate(name_lower=Lower("name"))
                .filter(**same_name)
                .exclude(pk=self.pk)
                .exists()
            ):
                raise ValidationError({"name": "A DNS forwarding rule with this name already exists in this view."})
            if DNSZone.objects.annotate(name_lower=Lower("name")).filter(**same_name).exists():
                raise ValidationError(
                    {
                        "name": "A DNS zone with this name exists in this view. "
                        "A rule cannot replace an authoritative zone."
                    }
                )

        if (
            self.action == DNSForwardingRuleActionChoices.ACTION_DO_NOT_FORWARD
            and self.present_in_database
            and self.forwarder_assignments.exists()
        ):
            raise ValidationError(
                {"action": "Remove this rule's forwarders before setting the action to Do not forward."}
            )

    def get_warnings(self):
        """Return problems that make this rule ineffective. None of them block saving.

        Returns:
            (list[str]): Human-readable warnings.
        """
        if self.action == DNSForwardingRuleActionChoices.ACTION_DO_NOT_FORWARD:
            return []

        warnings = []
        if not self.forwarder_assignments.exists():
            warnings.append("No forwarders are assigned, so this rule has nowhere to send queries.")

        if not self.is_global:
            zone = DNSZone.find_enclosing_zone(self.name, self.dns_view_id)
            rule_fqdn = normalize_dns_name(self.name)
            if zone is not None and not any(
                is_same_or_subdomain(rule_fqdn, delegation.fqdn) for delegation in zone.get_delegations()
            ):
                warnings.append(
                    f"{self.name} is inside zone {zone.name} in the same view, and that zone has no delegation for "
                    "it. BIND and Microsoft DNS answer such names from the zone instead of forwarding them."
                )
        return warnings


@extras_features("graphql")
class DNSForwardingRuleIPAddressAssignment(BaseModel):
    """Through model assigning an IP address, with port and order, to a DNS forwarding rule as a forwarder."""

    forwarding_rule = models.ForeignKey(
        to=DNSForwardingRule,
        on_delete=models.CASCADE,
        related_name="forwarder_assignments",
        verbose_name="Forwarding Rule",
    )
    ip_address = models.ForeignKey(
        to="ipam.IPAddress",
        on_delete=models.CASCADE,
        related_name="dns_forwarding_rule_assignments",
        verbose_name="IP Address",
    )
    port = models.PositiveIntegerField(
        default=53,
        validators=[MinValueValidator(1), MaxValueValidator(65535)],
        help_text="Port the forwarder listens on.",
    )
    weight = models.PositiveSmallIntegerField(
        default=100,
        help_text=(
            "Forwarders are listed from lowest to highest weight. "
            "Servers that query forwarders in order, such as Microsoft DNS, use this order."
        ),
    )

    class Meta:
        """Meta attributes for DNSForwardingRuleIPAddressAssignment."""

        ordering = ["forwarding_rule", "weight", "port"]
        unique_together = [["forwarding_rule", "ip_address", "port"]]
        verbose_name = "DNS Forwarding Rule IP Address Assignment"
        verbose_name_plural = "DNS Forwarding Rule IP Address Assignments"

    def __str__(self):
        """Stringify instance."""
        return f"{self.forwarding_rule}: {self.ip_address.host} port {self.port}"

    def clean(self):
        """Reject forwarders on rules that do not forward."""
        super().clean()
        if (
            self.forwarding_rule_id
            and self.forwarding_rule.action == DNSForwardingRuleActionChoices.ACTION_DO_NOT_FORWARD
        ):
            raise ValidationError("A rule with the action Do not forward cannot have forwarders.")
