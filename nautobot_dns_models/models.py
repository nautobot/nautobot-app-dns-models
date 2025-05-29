"""Models for Nautobot DNS Models."""

from constance import config as constance_config
from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from nautobot.apps.models import PrimaryModel, extras_features
from nautobot.core.models.fields import ForeignKeyWithAutoRelatedName


class DNSModel(PrimaryModel):
    """Abstract Model for Nautobot DNS Models."""

    #
    # name is effectively a NOOP here; it's overridden in both subclasses but
    # is here so that linters don't complain about it being used in clean().
    name = models.CharField(max_length=200)
    ttl = models.IntegerField(
        validators=[MinValueValidator(300), MaxValueValidator(2147483647)], default=3600, help_text="Time To Live."
    )

    class Meta:
        """Meta class."""

        abstract = True

    def __str__(self):
        """Stringify instance."""
        return self.name  # pylint: disable=no-member

    def clean(self):
        """Validate the name conforms to DNS label length restrictions.

        DNS name length restrictions (RFC 1035 §3.1):
        - Each label is limited to 63 octets
        - Empty labels are not allowed
        """
        super().clean()

        enforce_rfc1035_length = constance_config.nautobot_dns_models__ENFORCE_RFC1035_LENGTH

        if not enforce_rfc1035_length:
            return

        # Split name into labels
        label_list = self.name.split(".")

        # Check each label
        for label in label_list:
            if len(label) > 63:
                raise ValidationError({"name": f"Label '{label}' exceeds maximum length of 63 characters"})
            if not label:
                raise ValidationError({"name": "Empty labels are not allowed"})


@extras_features(
    "custom_fields",
    "custom_links",
    "custom_validators",
    "export_templates",
    "graphql",
    "relationships",
    "webhooks",
)
class DNSZoneModel(DNSModel):
    """Model for DNS SOA Records. An SOA Record defines a DNS Zone."""

    name = models.CharField(max_length=200, help_text="FQDN of the Zone, w/ TLD. e.g example.com", unique=True)
    filename = models.CharField(max_length=200, help_text="Filename of the Zone File.")
    description = models.TextField(help_text="Description of the Zone.", blank=True)
    soa_mname = models.CharField(
        max_length=200,
        help_text="FQDN of the Authoritative Name Server for Zone.",
        null=False,
    )
    soa_rname = models.EmailField(help_text="Admin Email for the Zone in the form")
    soa_refresh = models.IntegerField(
        validators=[MinValueValidator(300), MaxValueValidator(2147483647)],
        default=86400,
        help_text="Number of seconds after which secondary name servers should query the master for the SOA record, to detect zone changes.",
    )
    soa_retry = models.IntegerField(
        validators=[MinValueValidator(300), MaxValueValidator(2147483647)],
        default=7200,
        help_text="Number of seconds after which secondary name servers should retry to request the serial number from the master if the master does not respond.",
    )
    soa_expire = models.IntegerField(
        validators=[MinValueValidator(300), MaxValueValidator(2147483647)],
        default=3600000,
        help_text="Number of seconds after which secondary name servers should stop answering request for this zone if the master does not respond. This value must be bigger than the sum of Refresh and Retry.",
    )
    soa_serial = models.IntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(2147483647)],
        default=0,
        help_text="Serial number of the zone. This value must be incremented each time the zone is changed, and secondary DNS servers must be able to retrieve this value to check if the zone has been updated.",
    )
    soa_minimum = models.IntegerField(
        validators=[MinValueValidator(300), MaxValueValidator(2147483647)],
        default=3600,
        help_text="Minimum TTL for records in this zone.",
    )

    class Meta:
        """Meta attributes for DNSZoneModel."""

        verbose_name = "DNS Zone"
        verbose_name_plural = "DNS Zones"


class DNSRecordModel(DNSModel):  # pylint: disable=too-many-ancestors
    """Primary Dns Record model for plugin."""

    name = models.CharField(max_length=200, help_text="FQDN of the Record, w/o TLD.")
    zone = ForeignKeyWithAutoRelatedName(DNSZoneModel, on_delete=models.PROTECT)
    description = models.TextField(help_text="Description of the Record.", blank=True)
    comment = models.CharField(max_length=200, help_text="Comment for the Record.", blank=True)

    def clean(self):
        """Validate the record name conforms to DNS label length restrictions.

        DNS name length restrictions (RFC 1035 §3.1):
        - Each label is limited to 63 octets
        - The total length of an FQDN is limited to 255 octets
        - The length of each label is stored in a single octet
        - The final length octet must be zero (root)

        Wire format calculation:
        - Each label: 1 length octet + label content
        - Final root: 1 octet (zero length)
        - Total must not exceed 255 octets
        """
        super().clean()

        enforce_rfc1035_length = constance_config.nautobot_dns_models__ENFORCE_RFC1035_LENGTH

        if not enforce_rfc1035_length:
            return

        if not hasattr(self, "zone"):
            raise ValidationError({"zone": "Zone is required"})

        record_label_list = self.name.split(".")
        zone_label_list = self.zone.name.split(".")

        # Calculate wire format length including zone name
        # - 1 length octet + label length for each record label
        # - 1 length octet + label length for each zone label
        # - 1 octet for root label (zero length)
        wire_length = (
            sum(1 + len(record_label) for record_label in record_label_list)
            + sum(1 + len(zone_label) for zone_label in zone_label_list)
            + 1
        )
        if wire_length > 255:
            raise ValidationError({"name": "Total length of DNS name cannot exceed 255 characters"})

    class Meta:
        """Meta attributes for DnsRecordModel."""

        abstract = True


@extras_features(
    "custom_fields",
    "custom_links",
    "custom_validators",
    "export_templates",
    "graphql",
    "relationships",
    "webhooks",
)
class NSRecordModel(DNSRecordModel):  # pylint: disable=too-many-ancestors
    """NS Record model."""

    server = models.CharField(max_length=200, help_text="FQDN of an authoritative Name Server.")

    class Meta:
        """Meta attributes for NSRecordModel."""

        unique_together = [["name", "server", "zone"]]
        verbose_name = "NS Record"
        verbose_name_plural = "NS Records"


@extras_features(
    "custom_fields",
    "custom_links",
    "custom_validators",
    "export_templates",
    "graphql",
    "relationships",
    "webhooks",
)
class ARecordModel(DNSRecordModel):  # pylint: disable=too-many-ancestors
    """A Record model."""

    address = models.ForeignKey(to="ipam.IPAddress", on_delete=models.CASCADE, help_text="IP address for the record.")

    class Meta:
        """Meta attributes for ARecordModel."""

        unique_together = [["name", "address", "zone"]]
        verbose_name = "A Record"
        verbose_name_plural = "A Records"


@extras_features(
    "custom_fields",
    "custom_links",
    "custom_validators",
    "export_templates",
    "graphql",
    "relationships",
    "webhooks",
)
class AAAARecordModel(DNSRecordModel):  # pylint: disable=too-many-ancestors
    """AAAA Record model."""

    address = models.ForeignKey(to="ipam.IPAddress", on_delete=models.CASCADE, help_text="IP address for the record.")

    class Meta:
        """Meta attributes for AAAARecordModel."""

        unique_together = [["name", "address", "zone"]]
        verbose_name = "AAAA Record"
        verbose_name_plural = "AAAA Records"


@extras_features(
    "custom_fields",
    "custom_links",
    "custom_validators",
    "export_templates",
    "graphql",
    "relationships",
    "webhooks",
)
class CNAMERecordModel(DNSRecordModel):  # pylint: disable=too-many-ancestors
    """CNAME Record model."""

    alias = models.CharField(max_length=200, help_text="FQDN of the Alias.")

    class Meta:
        """Meta attributes for CNAMERecordModel."""

        unique_together = [["name", "alias", "zone"]]
        verbose_name = "CNAME Record"
        verbose_name_plural = "CNAME Records"


@extras_features(
    "custom_fields",
    "custom_links",
    "custom_validators",
    "export_templates",
    "graphql",
    "relationships",
    "webhooks",
)
class MXRecordModel(DNSRecordModel):  # pylint: disable=too-many-ancestors
    """MX Record model."""

    preference = models.IntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(65535)],
        default=10,
        help_text="Preference for the MX Record.",
    )
    mail_server = models.CharField(max_length=200, help_text="FQDN of the Mail Server.")

    class Meta:
        """Meta attributes for MXRecordModel."""

        unique_together = [["name", "mail_server", "zone"]]
        verbose_name = "MX Record"
        verbose_name_plural = "MX Records"


@extras_features(
    "custom_fields",
    "custom_links",
    "custom_validators",
    "export_templates",
    "graphql",
    "relationships",
    "webhooks",
)
class TXTRecordModel(DNSRecordModel):  # pylint: disable=too-many-ancestors
    """TXT Record model."""

    text = models.CharField(max_length=256, help_text="Text for the TXT Record.")

    class Meta:
        """Meta attributes for TXTRecordModel."""

        unique_together = [["name", "text", "zone"]]
        verbose_name = "TXT Record"
        verbose_name_plural = "TXT Records"


@extras_features(
    "custom_fields",
    "custom_links",
    "custom_validators",
    "export_templates",
    "graphql",
    "relationships",
    "webhooks",
)
class PTRRecordModel(DNSRecordModel):  # pylint: disable=too-many-ancestors
    """PTR Record model."""

    ptrdname = models.CharField(
        max_length=200, help_text="A domain name that points to some location in the domain name space."
    )

    class Meta:
        """Meta attributes for PTRRecordModel."""

        unique_together = [["name", "ptrdname", "zone"]]
        verbose_name = "PTR Record"
        verbose_name_plural = "PTR Records"

    def __str__(self):
        """String representation of PTRRecordModel."""
        return self.ptrdname


@extras_features(
    "custom_fields",
    "custom_links",
    "custom_validators",
    "export_templates",
    "graphql",
    "relationships",
    "webhooks",
)
class SRVRecordModel(DNSRecordModel):  # pylint: disable=too-many-ancestors
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
        """Meta attributes for SRVRecordModel."""

        unique_together = [["name", "target", "port", "zone"]]
        verbose_name = "SRV Record"
        verbose_name_plural = "SRV Records"
