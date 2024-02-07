"""Models for Nautobot DNS Models."""

# Django imports
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.urls import reverse


# Nautobot imports
from nautobot.core.models.fields import AutoSlugField
from nautobot.apps.models import BaseModel, PrimaryModel
from nautobot.extras.models.change_logging import ChangeLoggedModel


# from nautobot.extras.utils import extras_features
# If you want to use the extras_features decorator please reference the following documentation
# https://nautobot.readthedocs.io/en/latest/plugins/development/#using-the-extras_features-decorator-for-graphql
# Then based on your reading you may decide to put the following decorator before the declaration of your class
# @extras_features("custom_fields", "custom_validators", "relationships", "graphql")

# If you want to choose a specific model to overload in your class declaration, please reference the following documentation:
# how to chose a database model: https://nautobot.readthedocs.io/en/stable/plugins/development/#database-models

# class DnsModel


class DnsModel(PrimaryModel):  # pylint: disable=too-many-ancestors
    """Abstract Model for Nautobot DNS Models."""

    class Meta:
        """Meta class."""

        abstract = True

        # Option for fixing capitalization (i.e. "Snmp" vs "SNMP")
        # verbose_name = "Nautobot DNS Models"

        # Option for fixing plural name (i.e. "Chicken Tenders" vs "Chicken Tendies")
        # verbose_name_plural = "Nautobot DNS Modelss"

    # def get_absolute_url(self):
    #     """Return detail view for DnsZoneModel."""
    #     return reverse("plugins:nautobot_dns_models:dnszonemodel", args=[self.pk])

    def __str__(self):
        """Stringify instance."""
        return self.name


class DnsZoneModel(PrimaryModel):  # pylint: disable=too-many-ancestors
    """Model for DNS SOA Records. An SOA Record defines a DNS Zone."""

    name = models.CharField(max_length=200, help_text="FQDN of the Zone, w/ TLD.")
    slug = AutoSlugField(populate_from="name")
    ttl = models.IntegerField(
        validators=[MinValueValidator(300), MaxValueValidator(2147483647)], default=3600, help_text="Time To Live."
    )
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
        default="86400",
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

    def get_absolute_url(self):
        """Return the canonical URL for DnsZoneModel."""
        return reverse("plugins:nautobot_dns_models:dnszonemodel", args=[self.pk])


class DnsRecordModel(DnsModel):  # pylint: disable=too-many-ancestors
    """Primary Dns Record model for plugin."""

    name = models.CharField(max_length=200, help_text="FQDN of the Record, w/o TLD.")
    zone = models.ForeignKey(
        DnsZoneModel, on_delete=models.PROTECT, related_name="%(class)s", related_query_name="%(class)s"
    )
    ttl = models.IntegerField(
        validators=[MinValueValidator(300), MaxValueValidator(2147483647)], default=3600, help_text="Time To Live."
    )
    description = models.TextField(help_text="Description of the Record.", blank=True)
    comment = models.CharField(max_length=200, help_text="Comment for the Record.")

    class Meta:
        """Meta attributes for DnsRecordModel."""

        abstract = True


class NSRecordModel(DnsRecordModel):  # pylint: disable=too-many-ancestors
    """NS Record model."""

    server = models.CharField(max_length=200, help_text="FQDN of an authoritative Name Server.")
    slug = AutoSlugField(populate_from="name")

    def get_absolute_url(self):
        """Return the canonical URL for NSRecordModel."""
        return reverse("plugins:nautobot_dns_models:nsrecordmodel", args=[self.pk])

    def __str__(self):
        """String representation of NSRecordModel."""
        return self.name


class ARecordModel(DnsRecordModel):  # pylint: disable=too-many-ancestors
    """A Record model."""

    address = models.ForeignKey(to="ipam.IPAddress", on_delete=models.CASCADE, help_text="IP address for the record.")
    slug = AutoSlugField(populate_from="name")

    def get_absolute_url(self):
        """Return the canonical URL for ARecordModel."""
        return reverse("plugins:nautobot_dns_models:arecordmodel", args=[self.pk])

    def __str__(self):
        """String representation of ARecordModel."""
        return self.name


class AAAARecordModel(DnsRecordModel):  # pylint: disable=too-many-ancestors
    """AAAA Record model."""

    address = models.ForeignKey(to="ipam.IPAddress", on_delete=models.CASCADE, help_text="IP address for the record.")
    slug = AutoSlugField(populate_from="name")

    def get_absolute_url(self):
        """Return the canonical URL for AAAARecordModel."""
        return reverse("plugins:nautobot_dns_models:aaaarecordmodel", args=[self.pk])

    def __str__(self):
        """String representation of AAAARecordModel."""
        return self.name


class CNAMERecordModel(DnsRecordModel):  # pylint: disable=too-many-ancestors
    """CNAME Record model."""

    alias = models.CharField(max_length=200, help_text="FQDN of the Alias.")
    slug = AutoSlugField(populate_from="name")

    def get_absolute_url(self):
        """Return the canonical URL for CNAMERecordModel."""
        return reverse("plugins:nautobot_dns_models:cnamerecordmodel", args=[self.pk])

    def __str__(self):
        """String representation of CNAMERecordModel."""
        return self.name


class MXRecordModel(DnsRecordModel):  # pylint: disable=too-many-ancestors
    """MX Record model."""

    preference = models.IntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(65535)],
        default=10,
        help_text="Preference for the MX Record.",
    )
    mail_server = models.CharField(max_length=200, help_text="FQDN of the Mail Server.")
    slug = AutoSlugField(populate_from="name")

    def get_absolute_url(self):
        """Return the canonical URL for MXRecordModel."""
        return reverse("plugins:nautobot_dns_models:mxrecordmodel", args=[self.pk])

    def __str__(self):
        """String representation of MXRecordModel."""
        return self.name


class TXTRecordModel(DnsRecordModel):  # pylint: disable=too-many-ancestors
    """TXT Record model."""

    text = models.CharField(max_length=256, help_text="Text for the TXT Record.")
    slug = AutoSlugField(populate_from="name")

    def get_absolute_url(self):
        """Return the canonical URL for TXTRecordModel."""
        return reverse("plugins:nautobot_dns_models:txtrecordmodel", args=[self.pk])

    def __str__(self):
        """String representation of TXTRecordModel."""
        return self.name


class PTRRecordModel(DnsRecordModel):
    """PTR Record model."""

    ptrdname = models.CharField(
        max_length=200, help_text="A domain name that points to some location in the domain name space."
    )
    slug = AutoSlugField(populate_from="name")

    def get_absolute_url(self):
        """Return the canonical URL for PTRRecordModel."""
        return reverse("plugins:nautobot_dns_models:ptrrecordmodel", args=[self.pk])

    def __str__(self):
        """String representation of PTRRecordModel."""
        return self.ptrdname
