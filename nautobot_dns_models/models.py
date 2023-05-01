"""Models for Nautobot DNS Models."""

# Django imports
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.urls import reverse


# Nautobot imports
from nautobot.core.fields import AutoSlugField
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


# class DnsModel(PrimaryModel):
#     """Abstract Model for Nautobot DNS Models."""


#     class Meta:
#         """Meta class."""

#         abstract = True

#         # Option for fixing capitalization (i.e. "Snmp" vs "SNMP")
#         # verbose_name = "Nautobot DNS Models"

#         # Option for fixing plural name (i.e. "Chicken Tenders" vs "Chicken Tendies")
#         # verbose_name_plural = "Nautobot DNS Modelss"

#     # def get_absolute_url(self):
#     #     """Return detail view for DnsZoneModel."""
#     #     return reverse("plugins:nautobot_dns_models:dnszonemodel", args=[self.slug])

#     def __str__(self):
#         """Stringify instance."""
#         return self.name


class DnsZoneModel(PrimaryModel):
    """Model for DNS SOA Records. An SOA Record defines a DNS Zone"""

    name = models.CharField(max_length=200, help_text="FQDN of the Zone, w/ TLD.")
    slug = AutoSlugField(populate_from="name")
    ttl = models.IntegerField(
        validators=[MinValueValidator(300), MaxValueValidator(2147483647)], default=3600, help_text="Time To Live."
    )

    mname = models.CharField(max_length=200, help_text="FQDN of the Authoritative Name Server for Zone.")
    rname = models.EmailField(help_text="Admin Email for the Zone in the form user@zone.tld.")
    refresh = models.IntegerField(
        validators=[MinValueValidator(300), MaxValueValidator(2147483647)],
        default="86400",
        help_text="Number of seconds after which secondary name servers should query the master for the SOA record, to detect zone changes.",
    )
    retry = models.IntegerField(
        validators=[MinValueValidator(300), MaxValueValidator(2147483647)],
        default=7200,
        help_text="Number of seconds after which secondary name servers should retry to request the serial number from the master if the master does not respond.",
    )
    expire = models.IntegerField(
        validators=[MinValueValidator(300), MaxValueValidator(2147483647)],
        default=3600000,
        help_text="Number of seconds after which secondary name servers should stop answering request for this zone if the master does not respond. This value must be bigger than the sum of Refresh and Retry.",
    )


# class DnsRecordModel(DnsModel):
#     """Abstract Model for DNS Records.
#     """

#     class Meta:
#         abstract=True


class NSRecordModel(PrimaryModel):
    """Model for DNS NS Records."""

    server = models.CharField(max_length=200, help_text="FQDN of an authoratative Name Server.")
    zone = models.ForeignKey(DnsZoneModel, on_delete=models.PROTECT)
    slug = AutoSlugField(populate_from="name")
    ttl = models.IntegerField(
        validators=[MinValueValidator(300), MaxValueValidator(2147483647)], default=3600, help_text="Time To Live."
    )


class ARecordModel(PrimaryModel):
    """Model for DNS A Records."""

    address = models.ForeignKey(to="ipam.IPAddress", on_delete=models.CASCADE, help_text="IP address for the record.")
    zone = models.ForeignKey(DnsZoneModel, on_delete=models.PROTECT)
    slug = AutoSlugField(populate_from="name")
    ttl = models.IntegerField(
        validators=[MinValueValidator(300), MaxValueValidator(2147483647)], default=3600, help_text="Time To Live."
    )

    def get_absolute_url(self):
        return reverse("plugins:nautobot_example_dns_manager:arecordmodel", args=[self.slug])

    def __str__(self):
        return self.name


class AAAARecordModel(PrimaryModel):
    """Model for DNS AAAA Records."""

    address = models.ForeignKey(to="ipam.IPAddress", on_delete=models.CASCADE, help_text="IP address for the record.")
    zone = models.ForeignKey(DnsZoneModel, on_delete=models.PROTECT)
    slug = AutoSlugField(populate_from="name")
    ttl = models.IntegerField(
        validators=[MinValueValidator(300), MaxValueValidator(2147483647)], default=3600, help_text="Time To Live."
    )

    def get_absolute_url(self):
        return reverse("plugins:nautobot_example_dns_manager:aaaarecordmodel", args=[self.slug])

    def __str__(self):
        return self.name


class MXRecordModel(PrimaryModel):
    """Model representing MX records."""

    priority = models.PositiveIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(65535)],
        default=10,
        help_text="Distance/Priority/Preference of the MX Record.",
    )
    value = models.CharField(help_text="FQDN of the mail-server.", max_length=253)

    zone = models.ForeignKey(DnsZoneModel, on_delete=models.PROTECT)
    slug = AutoSlugField(populate_from="name")
    ttl = models.IntegerField(
        validators=[MinValueValidator(300), MaxValueValidator(2147483647)], default=3600, help_text="Time To Live."
    )

    def get_absolute_url(self):
        return reverse("plugins:nautobot_example_dns_manager:mxrecordmodel", args=[self.slug])

    def __str__(self):
        return self.name


class CNameRecordModel(PrimaryModel):
    """Model representing CName records."""

    value = models.CharField(help_text="FQDN of where the CName record redirects to.", max_length=253)
    zone = models.ForeignKey(DnsZoneModel, on_delete=models.PROTECT)
    slug = AutoSlugField(populate_from="name")
    ttl = models.IntegerField(
        validators=[MinValueValidator(300), MaxValueValidator(2147483647)], default=3600, help_text="Time To Live."
    )

    def get_absolute_url(self):
        return reverse("plugins:nautobot_example_dns_manager:cnamerecordmodel", args=[self.slug])

    def __str__(self):
        return self.name


class PTRRecordModel(PrimaryModel):
    """Model representing PTR records."""

    # TODO: Implement a clean to grab the address and format as a PTR record

    address = models.ForeignKey(to="ipam.IPAddress", on_delete=models.CASCADE, help_text="IP address for the record.")
    value = models.CharField(help_text="FQDN of where the PTR record.", max_length=253)
    zone = models.ForeignKey(DnsZoneModel, on_delete=models.PROTECT)
    slug = AutoSlugField(populate_from="name")
    ttl = models.IntegerField(
        validators=[MinValueValidator(300), MaxValueValidator(2147483647)], default=3600, help_text="Time To Live."
    )

    def get_absolute_url(self):
        return reverse("plugins:nautobot_example_dns_manager:ptrrecordmodel", args=[self.slug])

    def __str__(self):
        return self.name


class TXTRecordModel(PrimaryModel):
    """Model representing TXT records."""

    value = models.CharField(help_text="Value of the Text Record.", max_length=256)
    zone = models.ForeignKey(DnsZoneModel, on_delete=models.PROTECT)
    slug = AutoSlugField(populate_from="value")
    ttl = models.IntegerField(
        validators=[MinValueValidator(300), MaxValueValidator(2147483647)], default=3600, help_text="Time To Live."
    )

    def get_absolute_url(self):
        return reverse("plugins:nautobot_example_dns_manager:txtrecordmodel", args=[self.slug])

    def __str__(self):
        return self.name
