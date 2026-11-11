"""Models for Nautobot DNS Models."""
# pylint: disable=too-many-lines

import base64
import hashlib
import uuid

from constance import config as constance_config
from django.apps import apps
from django.core.exceptions import NON_FIELD_ERRORS, ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator, validate_email
from django.db import models, transaction
from django.db.models import ProtectedError, Q
from django.db.models.functions import Lower
from nautobot.apps.models import BaseManager, BaseModel, PrimaryModel, RestrictedQuerySet, extras_features
from nautobot.core.models.fields import ForeignKeyWithAutoRelatedName
from nautobot.extras.models import StatusField
from nautobot.extras.signals import change_context_state
from nautobot.ipam.choices import IPAddressVersionChoices
from netutils.ip import ipaddress_address

from nautobot_dns_models.choices import DNSZoneTypeChoices
from nautobot_dns_models.system_writes import system_write, system_write_in_progress

# Reverse-DNS roots per RFC 1035 §3.5 and RFC 3596 §2.5
RESERVED_ROOTS = {"in-addr.arpa", "ip6.arpa", "arpa"}

# All DNS integer fields use the full unsigned 32-bit range (0..4294967295).
# RFC 8767 §4 defines TTL as a 32-bit unsigned integer (updating RFC 2181).
# RFC 1035 §3.3.13 defines SOA fields as 32-bit values, explicitly unsigned for SERIAL and MINIMUM;
# RFC 1982 §7 specifies SERIAL's uint32 range and arithmetic.
UINT32_MAX = 2**32 - 1

SYSTEM_MANAGED_DELETE_ERROR = "System-managed records cannot be deleted directly."
CATALOG_MEMBER_DELETE_ERROR = "Deleting a member zone requires permission to change its catalog zone."

# Zone apex per RFC 1035 §5.1.
APEX_RECORD_NAME = "@"

# RFC 9432 §4 requires an NS RRset in a catalog zone so that it is a syntactically valid zone, and
# recommends a single RR naming "invalid.". Stored without the trailing dot the RFC writes: a name
# server is an absolute domain name here, and the dot is presentation syntax rather than data.
CATALOG_APEX_NS_SERVER = "invalid"

# RFC 9432 §4.1: TTLs in a catalog zone carry no meaning, and the RFC sets them to zero.
CATALOG_RECORD_TTL = 0

# RFC 1035 §3.3 defines a <character-string> as a length octet followed by up to 255 octets.
TXT_CHARACTER_STRING_MAX_OCTETS = 255
# RFC 1035 §3.3.14, §4.1.3: TXT RDATA, including each length octet, has a limit of 16-bit RDLENGTH.
TXT_RDATA_MAX_OCTETS = 2**16 - 1

# RFC 1035 §2.3.3 and RFC 4343 §2: domain name comparisons are case-insensitive.
DNS_ZONE_NAME_UNIQUE_ERROR_CODE = "dns_zone_name_not_unique"

# The fields holding a zone's catalog membership, which only `DNSZone.save()` can keep consistent
# with the member PTR record it publishes.
CATALOG_MEMBERSHIP_FIELDS = {"catalog_zone", "catalog_zone_id", "member_label"}


def dns_wire_label_length(label):
    """Return the wire-format (IDNA/Punycode) length of a DNS label."""
    if label.isascii():
        return len(label)

    return len("xn--" + label.encode("punycode").decode("ascii"))


def _decode_txt_escapes(value, field="text"):
    r"""Decode a quoted <character-string> into wire octets: `\DDD` is one octet, `\X` is X (RFC 1035 §5.1)."""
    decoded = bytearray()
    index = 0
    while index < len(value):
        character = value[index]
        if character != "\\":
            decoded.extend(character.encode("utf-8"))
            index += 1
            continue

        escape = value[index + 1 : index + 4]
        if len(escape) == 3 and escape.isdigit():
            octet = int(escape)
            if octet > 255:
                raise ValidationError({field: rf"Invalid escape '\{escape}': decimal escapes must be 0-255."})
            decoded.append(octet)
            index += 4
            continue

        if index + 1 >= len(value):
            raise ValidationError({field: "Invalid trailing backslash in quoted character-string."})
        decoded.extend(value[index + 1].encode("utf-8"))
        index += 2

    return bytes(decoded)


def _parse_quoted_txt_character_strings(value, field="text"):
    """Parse whitespace-separated, double-quoted <character-string> values per RFC 1035 §5.1."""
    character_string_list = []
    index = 0
    length = len(value)
    while index < length:
        if value[index].isspace():
            index += 1
            continue
        if value[index] != '"':
            raise ValidationError(
                {field: "Expected a double-quoted character-string; mixing quoted and unquoted text is not supported."}
            )

        index += 1
        start = index
        while index < length:
            if value[index] == "\\":
                index += 2
                continue
            if value[index] == '"':
                break
            index += 1

        if index >= length:
            raise ValidationError({field: "Unterminated quoted character-string."})

        character_string_list.append(_decode_txt_escapes(value[start:index], field=field))
        index += 1

    if not character_string_list:
        raise ValidationError({field: "No character-strings found."})

    return character_string_list


def _chunk_utf8_octets(value, max_octets):
    """Split a string into UTF-8 encoded chunks of at most `max_octets` bytes, never splitting a character."""
    chunk_list = []
    current = []
    current_octets = 0
    for character in value:
        character_octets = len(character.encode("utf-8"))
        if current_octets + character_octets > max_octets:
            chunk_list.append("".join(current))
            current = []
            current_octets = 0
        current.append(character)
        current_octets += character_octets

    if current:
        chunk_list.append("".join(current))

    return [chunk.encode("utf-8") for chunk in chunk_list]


def split_txt_character_strings(value, field="text"):
    """Return `value` as TXT <character-string> values, each as wire-format `bytes` (RFC 1035 §3.3.14).

    A value starting with a double quote is parsed as presentation format (RFC 1035 §5.1);
    any other value is split into 255-octet chunks.
    """
    if value is None:
        return []

    if value.lstrip().startswith('"'):
        return _parse_quoted_txt_character_strings(value.strip(), field=field)

    if value == "":
        return [b""]

    return _chunk_utf8_octets(value, TXT_CHARACTER_STRING_MAX_OCTETS)


def txt_wire_rdata_length(character_string_list):
    """Return the wire-format TXT RDATA length: each <character-string> plus its length octet."""
    return sum(1 + len(character_string) for character_string in character_string_list)


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


def catalog_member_label():
    """Return a new opaque DNS label for a catalog zone member.

    RFC 9432 §4.1 lets a producer pick any unique label and treats it as the member's identity
    for consumer state. A fresh UUID encoded as unpadded lowercase base32 yields 26 DNS-safe
    characters (a-z, 2-7), well inside the 63-octet label limit.
    """
    return base64.b32encode(uuid.uuid4().bytes).decode("ascii").rstrip("=").lower()


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


def dns_record_models():
    """Return every concrete DNSRecord subclass registered with Django."""
    return [model for model in apps.get_models() if issubclass(model, DNSRecord)]


def delete_member_ptr_records(member_ptr_records):
    """Delete each record in `member_ptr_records`, keeping its primary key on the deleted instance.

    The bulk edit job defers change logging and serializes each deleted instance only when the batch
    ends. Django clears a deleted instance's primary key, and a tagged model without one cannot be
    serialized, so the whole batch would fail.
    """
    for record in member_ptr_records:
        pk = record.pk
        record.delete()
        record.pk = pk


def acting_user():
    """Return the user the current change context attributes changes to, or None outside one.

    Nautobot opens a change context for every web request, API request and job, so this names
    the user behind a write wherever it starts, including the bulk edit job, whose form has no user.
    """
    change_context = change_context_state.get()
    if change_context is None:
        return None

    return change_context.get_user()


class DNSZoneQuerySet(RestrictedQuerySet):
    """QuerySet for DNSZone."""

    def bulk_create(self, objs, *args, **kwargs):
        """Refuse zones in a catalog, which would be stored without a member label or a published PTR."""
        objs = list(objs)
        if any(obj.catalog_zone_id for obj in objs):
            raise ValidationError(
                "Zones cannot be added to a catalog zone through bulk_create(); save each zone instead."
            )

        return super().bulk_create(objs, *args, **kwargs)

    def bulk_update(self, objs, fields, *args, **kwargs):
        """Refuse the membership fields, and renaming members, which this would write without publishing the member PTR."""
        # `update()` would refuse these too, but only inside Django's atomic block, leaving the caller's
        # transaction unusable.
        self._refuse_membership_fields(fields)
        objs = list(objs)
        if "name" in fields:
            # Stored membership, since an instance in hand may predate a change to its catalog.
            stored_zones = self.filter(pk__in=[obj.pk for obj in objs])
            stored_zones._refuse_member_renames()  # pylint: disable=protected-access

        return super().bulk_update(objs, fields, *args, **kwargs)

    def delete(self):
        """Withdraw member PTR records and clear system-managed records, then delete the zones."""
        with transaction.atomic():
            # Nothing protects the records in the purge, but if the delete fails (e.g. due to
            # PROTECT from a member zone), the records are restored.
            self.prepare_for_delete()
            return super().delete()

    def update(self, **kwargs):
        """Refuse the membership fields, and renaming members, which this would write without publishing the member PTR."""
        self._refuse_membership_fields(kwargs)
        if "name" in kwargs:
            self._refuse_member_renames()

        return super().update(**kwargs)

    def prepare_for_delete(self):
        """Refuse members whose catalog the acting user may not change, then withdraw their PTR records and clear system-managed records.

        Run it in the same transaction as the delete, so that a refused delete keeps the records.
        """
        self._refuse_member_deletes_without_catalog_permission()
        self._withdraw_member_ptr_records()
        self._purge_system_managed_records()

    def _purge_system_managed_records(self):
        """Delete the records of the catalog zones among these zones.

        Every record in a catalog zone is system-managed. `DNSRecord.zone` is PROTECT and those
        records refuse user deletes, so a catalog zone would otherwise be permanently undeletable.
        """
        managed_zone_pks = list(self.filter(type=DNSZoneTypeChoices.TYPE_CATALOG).values_list("pk", flat=True))
        if not managed_zone_pks:
            return

        with system_write():
            for record_model in dns_record_models():
                record_model.objects.filter(zone_id__in=managed_zone_pks).delete()

    def _refuse_member_deletes_without_catalog_permission(self):
        """Refuse to delete the members among these zones whose catalog zone the acting user may not change.

        Deleting a member withdraws its PTR record from the catalog, as removing it from the catalog does.
        Raises `ProtectedError`, which every delete path reports as a refusal. Outside a change context,
        as in a shell or a migration, there is no user to hold to it.
        """
        user = acting_user()
        if user is None:
            return

        refused = self.filter(catalog_zone__isnull=False).exclude(
            catalog_zone__in=DNSZone.objects.restrict(user, "change")
        )
        if refused.exists():
            raise ProtectedError(CATALOG_MEMBER_DELETE_ERROR, list(refused[:50]))

    def _refuse_member_renames(self):
        """Raise if this holds a catalog member, whose PTR record names it and which a rename gives a new label."""
        if self.filter(catalog_zone__isnull=False).exists():
            raise ValidationError("Catalog member zones cannot be renamed through a queryset; save each zone instead.")

    @staticmethod
    def _refuse_membership_fields(fields):
        """Raise if `fields` names a catalog membership field."""
        if refused := sorted(set(fields) & CATALOG_MEMBERSHIP_FIELDS):
            raise ValidationError(
                f"These fields cannot be written through a queryset; save each zone instead: {', '.join(refused)}."
            )

    def _withdraw_member_ptr_records(self):
        """Withdraw the PTR records of the catalog members among these zones.

        Reads the stored memberships, since an instance in hand may predate a change to its catalog.
        """
        for zone in self.filter(catalog_zone__isnull=False):
            zone.withdraw_member_ptr_record()


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

    @staticmethod
    def _validate_dns_label(label, field="name"):
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
    portal_url = models.URLField(
        max_length=500, blank=True, help_text="Registrar portal URL.", verbose_name="Portal URL"
    )
    account_number = models.CharField(max_length=100, blank=True, help_text="Registrar account number.")

    class Meta:
        """Meta attributes for DNSRegistrar."""

        verbose_name = "DNS Registrar"
        verbose_name_plural = "DNS Registrars"

    def __str__(self):
        """Stringify instance."""
        return self.name


def get_default_view():
    """Return the default DNSView instance, creating it if necessary."""
    default_view, _ = DNSView.objects.get_or_create(
        name="Default", defaults={"description": "Default DNS view. Created by Nautobot DNS Models app."}
    )
    return default_view


def get_default_view_pk():
    """Return the default DNSView ID, creating it if necessary."""
    return get_default_view().pk


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
    type = models.CharField(
        max_length=50,
        choices=DNSZoneTypeChoices,
        default=DNSZoneTypeChoices.TYPE_PRIMARY,
        help_text="Type of the zone. Cannot be changed after creation.",
    )
    dns_view = ForeignKeyWithAutoRelatedName(
        DNSView,
        on_delete=models.PROTECT,
        help_text="The DNS View this Zone belongs to.",
        verbose_name="View",
        default=get_default_view_pk,
    )
    catalog_zone = models.ForeignKey(
        to="self",
        on_delete=models.PROTECT,
        related_name="members",
        blank=True,
        null=True,
        limit_choices_to={"type": DNSZoneTypeChoices.TYPE_CATALOG},
        help_text="The catalog zone this zone is a member of.",
        verbose_name="Catalog Zone",
    )
    member_label = models.CharField(
        max_length=63,
        blank=True,
        default="",
        editable=False,
        help_text=(
            "Opaque DNS label identifying this zone within its catalog zone. "
            "Generated when the zone is added to a catalog or renamed."
        ),
        verbose_name="Member Label",
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

    objects = BaseManager.from_queryset(DNSZoneQuerySet)()

    # The case-insensitive UniqueConstraint has no `fields`, so Nautobot cannot derive the natural key from it.
    natural_key_field_names = ["name", "dns_view"]

    class Meta:
        """Meta attributes for DNSZone."""

        constraints = [
            models.UniqueConstraint(
                Lower("name"),
                "dns_view",
                name="nautobot_dns_models_dnszone_name_ci_unique",
                violation_error_code=DNS_ZONE_NAME_UNIQUE_ERROR_CODE,
                violation_error_message="A DNS zone with this name (ignoring letter case) already exists in this view.",
            ),
            models.CheckConstraint(
                condition=~Q(type=DNSZoneTypeChoices.TYPE_CATALOG) | Q(auto_create_ptr=False),
                name="catalog_zone_no_auto_create_ptr",
                violation_error_message="Catalog zones cannot enable automatic PTR creation.",
                violation_error_code="catalog_zone_auto_create_ptr",
            ),
            # RFC 9432 says nothing about nested catalog zones, and most consumers do not support them.
            models.CheckConstraint(
                condition=Q(catalog_zone__isnull=True) | ~Q(type=DNSZoneTypeChoices.TYPE_CATALOG),
                name="catalog_zone_not_a_member",
                violation_error_message="A catalog zone cannot be a member of another catalog zone.",
            ),
            models.CheckConstraint(
                condition=(Q(catalog_zone__isnull=True) & Q(member_label=""))
                | (Q(catalog_zone__isnull=False) & ~Q(member_label="")),
                name="member_label_only_in_a_catalog",
                violation_error_message="A zone has a member label exactly when it is in a catalog zone.",
            ),
            # RFC 4343 §3 compares labels without regard to case, so labels differing only in case would
            # publish two PTR records at one owner name, where RFC 9432 §4.1 allows only one. Zones outside
            # a catalog all have a blank label, but a NULL `catalog_zone` keeps them apart.
            models.UniqueConstraint(
                "catalog_zone",
                Lower("member_label"),
                name="member_label_unique_in_catalog_case_insensitive",
                violation_error_message="This label is already used by another member of the catalog zone.",
            ),
        ]
        verbose_name = "DNS Zone"
        verbose_name_plural = "DNS Zones"

    def __str__(self):
        """Stringify instance."""
        return f"{self.name} ({self.dns_view})"

    def validate_constraints(self, exclude=None):
        """Report a zone name that collides with another zone in the same view as an error on `name`."""
        try:
            super().validate_constraints(exclude=exclude)
        except ValidationError as error:
            errors = error.update_error_dict({})
            for non_field_error in errors.pop(NON_FIELD_ERRORS, []):
                field = "name" if non_field_error.code == DNS_ZONE_NAME_UNIQUE_ERROR_CODE else NON_FIELD_ERRORS
                errors.setdefault(field, []).append(non_field_error)
            raise ValidationError(errors) from error

    def clean(self):
        """Normalize the SOA RNAME, keep type immutable, bar catalog PTR, and validate catalog membership."""
        super().clean()

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

        self.soa_rname = normalized_soa_rname

        stored_zone = self._stored_zone()
        if stored_zone is not None:
            self._validate_type_unchanged(stored_zone.type)

        if self.is_catalog_zone and self.auto_create_ptr:
            raise ValidationError({"auto_create_ptr": "Catalog zones cannot enable automatic PTR creation."})

        # Before the constraints are validated, which hold the label to the catalog.
        self._enforce_membership_rules(stored_zone)

    def delete(self, *args, **kwargs):
        """Withdraw the member PTR record and clear system-managed records, then delete the zone."""
        with transaction.atomic():
            # Nothing protects the records in the purge, but if the zone delete fails (e.g. due to
            # PROTECT from a member zone), the records are restored.
            DNSZone.objects.filter(pk=self.pk).prepare_for_delete()
            return super().delete(*args, **kwargs)

    def save(self, *args, **kwargs):
        """Normalize the RNAME, then write the records this zone's type and catalog membership require.

        Adding a zone to a catalog, removing it, moving it to another catalog, and renaming a member
        publish the member PTR under a new label and withdraw the old one, which a consumer sees as a
        removal and an addition (RFC 9432 §5.4). If those records cannot be written, the zone is not
        saved either.

        Membership fields left out of `update_fields` take their stored values, so that the PTR
        record describes what is stored.
        """
        self.soa_rname = normalize_soa_rname(self.soa_rname)
        update_fields = kwargs.get("update_fields")

        with transaction.atomic():
            stored_zone = self._stored_zone(lock=True)
            if stored_zone is not None:
                self._validate_type_unchanged(stored_zone.type)
                if update_fields is not None:
                    # This is a safeguard against code that changes the name, view or catalog but leaves
                    # it out of `update_fields`.
                    #
                    #     zone.name = "renamed.example"
                    #     zone.save(update_fields=["description"])
                    #
                    # Here, Django would not save the name, but the code above would still give the zone a
                    # new label and a PTR record for that name. An unsaved catalog change does the same,
                    # publishing the PTR record in a catalog the zone is not stored in.
                    self._keep_unwritten_fields(stored_zone, update_fields)

            self._enforce_membership_rules(stored_zone, lock=True)
            if update_fields is not None and stored_zone is not None and self.member_label != stored_zone.member_label:
                kwargs["update_fields"] = {*update_fields, "member_label"}

            super().save(*args, **kwargs)
            self._reconcile_required_catalog_records()
            self._sync_member_ptr_record(stored_zone)

    @property
    def ptr_record_name(self):
        """Return the owner name this zone is published at in its catalog zone, or None outside a catalog."""
        # Relative to the catalog apex (RFC 9432 §4.1).
        return f"{self.member_label}.zones" if self.catalog_zone_id else None

    @property
    def is_catalog_zone(self):
        """Return whether this zone is an RFC 9432 catalog zone."""
        return self.type == DNSZoneTypeChoices.TYPE_CATALOG

    @classmethod
    def find_reverse_zone_for_ptrdname(cls, ptrdname, dns_view=None):
        """Return the most-specific reverse DNSZone whose name matches a tail of `ptrdname`, otherwise None."""
        labels = ptrdname.split(".")
        for i in range(1, len(labels)):
            zone_name = ".".join(labels[i:])
            # We shouldn't match those cause are reserved to IANA
            if zone_name in RESERVED_ROOTS:
                break

            zones = cls.objects.filter(name=zone_name).exclude(type=DNSZoneTypeChoices.TYPE_CATALOG)
            if dns_view is not None:
                zones = zones.filter(dns_view=dns_view)
            zone = zones.first()
            if zone:
                return zone
        return None

    def withdraw_member_ptr_record(self):
        """Withdraw the PTR record naming this member zone in its catalog zone."""
        with system_write():
            delete_member_ptr_records(PTRRecord.objects.filter(name=self.ptr_record_name, zone_id=self.catalog_zone_id))

    def _assign_member_label(self, stored_zone):
        """Set the member label this save requires, refusing a supplied label it cannot keep."""
        stored_label = stored_zone.member_label if stored_zone else ""
        if not self.catalog_zone_id:
            if self.member_label not in ("", stored_label):
                raise ValidationError({"member_label": "Only a zone in a catalog zone can have a member label."})
            self.member_label = ""
            return

        catalog_changed = stored_zone is None or stored_zone.catalog_zone_id != self.catalog_zone_id
        name_changed = stored_zone is not None and stored_zone.name != self.name
        if not (catalog_changed or name_changed):
            # Consumers identify the member by its label (RFC 9432 §4.1), so it changes only with the membership.
            if self.member_label != stored_label:
                raise ValidationError(
                    {
                        "member_label": "The member label can only be set when the zone is added to a catalog, "
                        "moved to another, or renamed."
                    }
                )
        # A supplied label is kept, so that `save()` keeps the label an earlier `clean()` generated and so that
        # code importing an existing catalog can keep its members' labels.
        elif not self.member_label or self.member_label == stored_label:
            self.member_label = catalog_member_label()

    def _enforce_membership_rules(self, stored_zone, *, lock=False):
        """Assign the member label, then refuse a label or catalog membership this zone cannot have.

        `save()` runs this as well as `clean()`, since code using the ORM can save without cleaning, and
        the member PTR record `save()` publishes must match what is stored.

        Args:
            stored_zone (DNSZone): This zone as stored, or None for a new zone.

        Keyword Args:
            lock (bool): Lock the catalog zone's row while reading it. Defaults to False.
        """
        self._assign_member_label(stored_zone)
        self._validate_member_label()
        self._validate_membership(stored_zone, lock=lock)

    def _keep_unwritten_fields(self, stored_zone, update_fields):
        """Reset the name, view and catalog to their stored values when `update_fields` leaves them out."""
        for attribute_name, names in (
            ("name", {"name"}),
            ("dns_view_id", {"dns_view", "dns_view_id"}),
            ("catalog_zone_id", {"catalog_zone", "catalog_zone_id"}),
        ):
            if names.isdisjoint(update_fields):
                setattr(self, attribute_name, getattr(stored_zone, attribute_name))

    def _publish_member_ptr_record(self):
        """Publish the PTR record naming this member zone in its catalog zone.

        RFC 9432 §4.1 allows only a single RR at that owner name, so anything else standing there gives way.
        """
        owner_name = self.ptr_record_name
        member_ptr_records = PTRRecord.objects.filter(name=owner_name, zone_id=self.catalog_zone_id)

        with system_write():
            delete_member_ptr_records(member_ptr_records.exclude(ptrdname=self.name))
            if not member_ptr_records.filter(ptrdname=self.name).exists():
                PTRRecord(
                    name=owner_name, ptrdname=self.name, zone_id=self.catalog_zone_id, _ttl=CATALOG_RECORD_TTL
                ).validated_save()

    def _reconcile_apex_ns_record(self):
        """Hold the apex NS RRset RFC 9432 §4 requires at the single `invalid.` RR it recommends."""
        ns_records = NSRecord.objects.filter(zone=self)
        ns_records.exclude(name=APEX_RECORD_NAME, server=CATALOG_APEX_NS_SERVER).delete()
        if not ns_records.exists():
            NSRecord(
                name=APEX_RECORD_NAME, server=CATALOG_APEX_NS_SERVER, zone=self, _ttl=CATALOG_RECORD_TTL
            ).validated_save()

    def _reconcile_required_catalog_records(self):
        """Hold this catalog zone's apex NS and `version` TXT records at what RFC 9432 requires.

        Idempotent, so saving the zone repairs those two records rather than only populating a
        brand-new catalog.
        """
        if not self.is_catalog_zone:
            return

        with system_write():
            self._reconcile_apex_ns_record()
            self._reconcile_version_record()

    def _reconcile_version_record(self):
        """Hold the schema version TXT at the single RR RFC 9432 §4.2.1 requires."""
        version_records = TXTRecord.objects.filter(name="version", zone=self)
        # "2" is the only version the RFC defines. A second RR in the version RRset makes the whole
        # catalog broken.
        version_records.exclude(text="2").delete()
        if not version_records.filter(text="2").exists():
            TXTRecord(name="version", text="2", zone=self, _ttl=CATALOG_RECORD_TTL).validated_save()

    def _stored_zone(self, *, lock=False):
        """Return this zone as stored, or None for a new zone.

        Keyword Args:
            lock (bool): Hold the row until the transaction ends. Defaults to False.
        """
        if not self.present_in_database:
            return None

        zones = DNSZone.objects.filter(pk=self.pk)
        if lock:
            # Locked so that a zone being added to this catalog, which locks this row to read its view, waits
            # for this save instead of slipping past the view check.
            zones = zones.select_for_update()

        return zones.first()

    def _sync_member_ptr_record(self, stored_zone):
        """Withdraw the PTR this zone was published under if its catalog or label changed, then publish the current one."""
        if stored_zone is not None and stored_zone.catalog_zone_id:
            if (stored_zone.catalog_zone_id, stored_zone.member_label) != (self.catalog_zone_id, self.member_label):
                stored_zone.withdraw_member_ptr_record()

        if self.catalog_zone_id:
            self._publish_member_ptr_record()

    def _validate_catalog_permission(self, catalog_zone_ids):
        """Require the acting user to be allowed to change every catalog zone in `catalog_zone_ids`.

        Outside a change context, as in a shell or a migration, there is no user to hold to it.
        """
        user = acting_user()
        if user is None or not catalog_zone_ids:
            return

        if DNSZone.objects.restrict(user, "change").filter(pk__in=catalog_zone_ids).count() != len(catalog_zone_ids):
            raise ValidationError(
                {
                    "catalog_zone": "Changing a zone's catalog requires permission to change the catalog zones it is added to or removed from."
                }
            )

    def _validate_member_label(self):
        """Require the label to be exactly one DNS label, since it names a single node in the catalog."""
        if "." in self.member_label:
            raise ValidationError({"member_label": "The member label must be a single DNS label, without dots."})

        if dns_wire_label_length(self.member_label) > 63:
            raise ValidationError(
                {"member_label": "The member label exceeds the maximum length of 63 bytes (octets) in wire format."}
            )

    def _validate_membership(self, stored_zone, *, lock=False):
        """Refuse a catalog membership RFC 9432 or this app cannot represent, or one the acting user may not make.

        Args:
            stored_zone (DNSZone): This zone as stored, or None for a new zone.

        Keyword Args:
            lock (bool): Lock the catalog zone's row while reading its type and view. Defaults to False.
        """
        stored_catalog_zone_id = stored_zone.catalog_zone_id if stored_zone else None
        moving = stored_zone is not None and stored_zone.dns_view_id != self.dns_view_id

        if self.is_catalog_zone:
            if self.catalog_zone_id:
                raise ValidationError({"catalog_zone": "A catalog zone cannot be a member of another catalog zone."})
            # Queried, not read from `members`, which answers from any prefetch.
            if moving and DNSZone.objects.filter(catalog_zone_id=self.pk).exists():
                raise ValidationError({"dns_view": "A catalog zone with members cannot be moved to another view."})
            return

        if self.catalog_zone_id and (self.catalog_zone_id != stored_catalog_zone_id or moving):
            catalogs = DNSZone.objects.filter(pk=self.catalog_zone_id)
            if lock:
                catalogs = catalogs.select_for_update()
            catalog = catalogs.values("type", "dns_view_id").first()

            if catalog is None:
                raise ValidationError({"catalog_zone": "The catalog zone no longer exists."})
            if catalog["type"] != DNSZoneTypeChoices.TYPE_CATALOG:
                raise ValidationError({"catalog_zone": "Zones can only be members of a catalog zone."})
            if catalog["dns_view_id"] != self.dns_view_id:
                raise ValidationError({"catalog_zone": "The catalog zone must be in the same view as this zone."})

        if self.catalog_zone_id != stored_catalog_zone_id:
            self._validate_catalog_permission({stored_catalog_zone_id, self.catalog_zone_id} - {None})

    def _validate_type_unchanged(self, stored_type):
        """Refuse a type that differs from the one already stored."""
        if stored_type != self.type:
            raise ValidationError({"type": "Zone type cannot be changed after creation."})


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

    def clean(self):
        """Ensure registration is not against a catalog zone."""
        super().clean()

        if self.dns_zone_id and self.dns_zone.is_catalog_zone:
            raise ValidationError({"dns_zone": "Catalog zones cannot be registered."})


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


class DNSRecordQuerySet(RestrictedQuerySet):
    """QuerySet shared by every concrete DNSRecord subclass."""

    def delete(self):
        """Refuse to delete system-managed records, as `DNSRecord.delete()` does for one record."""
        # Nautobot's bulk delete job calls `QuerySet.delete()` directly, bypassing `DNSRecord.delete()`.
        if not system_write_in_progress():
            protected = self.filter(zone__type=DNSZoneTypeChoices.TYPE_CATALOG)
            if protected.exists():
                raise ProtectedError(SYSTEM_MANAGED_DELETE_ERROR, list(protected[:50]))

        return super().delete()


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

    objects = BaseManager.from_queryset(DNSRecordQuerySet)()

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
        self._enforce_zone_type_allows_record()

    def delete(self, *args, **kwargs):
        """Refuse to delete a system-managed record."""
        if not system_write_in_progress() and self.zone.is_catalog_zone:
            raise ProtectedError(SYSTEM_MANAGED_DELETE_ERROR, [self])
        return super().delete(*args, **kwargs)

    def _validate_total_wire_length_if_enabled(self) -> None:
        """Validate full DNS name (record + zone) total wire-format length if wire-format validation is enabled."""
        validation_level = getattr(constance_config, "nautobot_dns_models__DNS_VALIDATION_LEVEL")
        if validation_level != "wire-format":
            return

        # An apex record contributes no labels of its own; the name is the zone's.
        record_label_list = [] if self.name in ("", APEX_RECORD_NAME) else self.name.split(".")
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

    def _enforce_zone_type_allows_record(self) -> None:
        """Reject a user write of a record type the zone's type does not make available to users."""
        if system_write_in_progress() or not self.zone.is_catalog_zone:  # pylint: disable=no-member
            return

        zone_type_label = self.zone.get_type_display().lower()  # pylint: disable=no-member
        raise ValidationError(
            {
                "zone": (
                    f"Records in a {zone_type_label} zone are system-managed and cannot be created or edited directly."
                )
            }
        )

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
    mail_server = models.CharField(max_length=200, help_text="FQDN of the Mail server.")

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

    text = models.TextField(help_text="Text for the TXT Record.")
    # SHA-256 hash of `text` for the unique constraint: MySQL cannot index a TEXT column without a prefix (error 1170).
    # The leading underscore keeps it out of the REST API, as with `_ttl`.
    _text_hash = models.CharField(
        max_length=64, editable=False, help_text="SHA-256 digest of `text`, used to enforce uniqueness."
    )

    # Declared explicitly, or Nautobot would derive the natural key from `unique_together` and use `_text_hash`.
    natural_key_field_names = ["name", "text", "zone"]

    class Meta:
        """Meta attributes for TXTRecord."""

        unique_together = [["name", "zone", "_text_hash"]]
        verbose_name = "TXT Record"
        verbose_name_plural = "TXT Records"

    @staticmethod
    def hash_text(value):
        """Return the SHA-256 digest used to enforce `text` uniqueness."""
        return hashlib.sha256((value or "").encode("utf-8")).hexdigest()

    @property
    def character_strings(self):
        """Return `text` as the list of <character-string> values it represents on the wire, each as `bytes`."""
        return split_txt_character_strings(self.text)

    def clean(self):
        """Refresh the uniqueness digest and validate `text` per RFC 1035 §3.3.14 if wire-format validation is enabled.

        The digest is set here, not only in `save()`, because `full_clean()` runs `clean()` before `validate_unique()`.
        """
        super().clean()

        self._text_hash = self.hash_text(self.text)

        validation_level = getattr(constance_config, "nautobot_dns_models__DNS_VALIDATION_LEVEL")
        if validation_level != "wire-format":
            return

        # Raises a ValidationError on `text` for malformed presentation format, e.g. an unterminated quote.
        character_string_list = split_txt_character_strings(self.text)
        for position, character_string in enumerate(character_string_list, start=1):
            octets = len(character_string)
            if octets > TXT_CHARACTER_STRING_MAX_OCTETS:
                raise ValidationError(
                    {
                        "text": (
                            f"Character-string {position} is {octets} bytes (octets) but the maximum is {TXT_CHARACTER_STRING_MAX_OCTETS}. "
                            'Split the value into multiple double-quoted character-strings, e.g. "part one" "part two".'
                        )
                    }
                )

        wire_length = txt_wire_rdata_length(character_string_list)
        if wire_length > TXT_RDATA_MAX_OCTETS:
            raise ValidationError(
                {
                    "text": (
                        f"Total TXT record data is {wire_length} bytes (octets) in wire format; the maximum is {TXT_RDATA_MAX_OCTETS}."
                    )
                }
            )

    def unique_error_message(self, model_class, unique_check):
        """Report a uniqueness violation in terms of `text` rather than the internal `_text_hash`."""
        if set(unique_check) == {"name", "zone", "_text_hash"}:
            return ValidationError(
                message="TXT Record with this Name, Zone and Text already exists.",
                code="unique_together",
            )
        return super().unique_error_message(model_class, unique_check)

    def save(self, *args, **kwargs):
        """Refresh the uniqueness digest before saving, for callers that bypass `clean()`."""
        self._text_hash = self.hash_text(self.text)
        # A caller updating only `text` would otherwise leave the digest behind in the database.
        update_fields = kwargs.get("update_fields")
        if update_fields is not None and "text" in update_fields:
            kwargs["update_fields"] = list(update_fields) + ["_text_hash"]
        super().save(*args, **kwargs)


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
