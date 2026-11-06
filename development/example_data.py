"""Populate Nautobot with example DNS Models data to showcase the app.

Run inside ``nautobot-server nbshell --plain`` (Django/ORM already configured), e.g. via
``invoke add-example-data``. Safe to run repeatedly: every object is created with a
get-or-create style lookup, so re-running neither errors on unique constraints nor
duplicates data.

Creates four forward zones, each with its own unique set of related objects: a DNS view,
a registrar, IPv4/IPv6 prefixes and addresses, a matching reverse zone, a registration, and
one of every record type (NS, A x2, AAAA, CNAME, MX, TXT, SRV, PTR).

NOTE: nbshell ``--plain`` evaluates this file line-by-line in an interactive console, where
a blank line ends the current indented block. Keep function/loop bodies free of blank lines;
blank lines and comments are only safe at module top level.
"""

from datetime import date

from django.contrib.contenttypes.models import ContentType
from nautobot.extras.models import Status
from nautobot.ipam.choices import PrefixTypeChoices
from nautobot.ipam.models import IPAddress, Namespace, Prefix

from nautobot_dns_models.models import (
    AAAARecord,
    ARecord,
    CNAMERecord,
    DNSRegistrar,
    DNSRegistration,
    DNSView,
    DNSZone,
    MXRecord,
    NSRecord,
    PTRRecord,
    SRVRecord,
    TXTRecord,
)

_RESULTS = []


def _record(label, created):
    """Record and echo whether an object was created or already present."""
    verb = "created" if created else "exists "
    print(f"  [{verb}] {label}")
    _RESULTS.append((label, created))
    return created


def _get_or_create_prefix(prefix_str, namespace, status):
    """Idempotently create a Prefix (looked up by network + length within the namespace)."""
    network, length = prefix_str.split("/")
    existing = Prefix.objects.filter(network=network, prefix_length=int(length), namespace=namespace).first()
    if existing:
        return existing, False
    prefix = Prefix.objects.create(prefix=prefix_str, namespace=namespace, status=status, type=PrefixTypeChoices.TYPE_NETWORK)
    return prefix, True


def _get_or_create_ip(address_str, namespace, status):
    """Idempotently create an IPAddress (looked up by host within the namespace)."""
    host = address_str.split("/")[0]
    existing = IPAddress.objects.filter(host=host, parent__namespace=namespace).first()
    if existing:
        return existing, False
    ip_address = IPAddress.objects.create(address=address_str, namespace=namespace, status=status)
    return ip_address, True


def build_zone(spec, status, namespace):
    """Create one forward zone plus its full, unique set of related DNS objects."""
    zone_fqdn = spec["zone"]
    print(f"\nZone {zone_fqdn}:")
    dns_view, created = DNSView.objects.get_or_create(name=spec["view"], defaults={"description": spec["view_desc"]})
    _record(f"DNSView {spec['view']}", created)
    prefix_v4, created = _get_or_create_prefix(spec["prefix_v4"], namespace, status)
    _record(f"Prefix {spec['prefix_v4']}", created)
    prefix_v6, created = _get_or_create_prefix(spec["prefix_v6"], namespace, status)
    _record(f"Prefix {spec['prefix_v6']}", created)
    dns_view.prefixes.add(prefix_v4, prefix_v6)
    ip_www_v4, created = _get_or_create_ip(spec["ip_www_v4"], namespace, status)
    _record(f"IPAddress {spec['ip_www_v4']}", created)
    ip_app_v4, created = _get_or_create_ip(spec["ip_app_v4"], namespace, status)
    _record(f"IPAddress {spec['ip_app_v4']}", created)
    ip_www_v6, created = _get_or_create_ip(spec["ip_www_v6"], namespace, status)
    _record(f"IPAddress {spec['ip_www_v6']}", created)
    registrar, created = DNSRegistrar.objects.get_or_create(name=spec["registrar"], defaults={"url": spec["reg_url"], "account_number": spec["reg_acct"]})
    _record(f"DNSRegistrar {spec['registrar']}", created)
    forward_zone, created = DNSZone.objects.get_or_create(name=zone_fqdn, dns_view=dns_view, defaults={"ttl": 3600, "filename": f"{zone_fqdn}.zone", "description": f"Example forward lookup zone for {zone_fqdn}.", "soa_mname": f"ns1.{zone_fqdn}.", "soa_rname": f"hostmaster@{zone_fqdn}"})
    _record(f"DNSZone {zone_fqdn}", created)
    reverse_zone, created = DNSZone.objects.get_or_create(name=spec["reverse_zone"], dns_view=dns_view, defaults={"ttl": 3600, "filename": f"{spec['reverse_zone']}.zone", "description": f"Example reverse lookup zone for {spec['prefix_v4']}.", "soa_mname": f"ns1.{zone_fqdn}.", "soa_rname": f"hostmaster@{zone_fqdn}"})
    _record(f"DNSZone {spec['reverse_zone']}", created)
    _, created = DNSRegistration.objects.get_or_create(dns_registrar=registrar, dns_zone=forward_zone, defaults={"status": status, "expiration_date": spec["expiration"], "auto_renewal": True, "privacy_enabled": True, "dnssec_enabled": True, "renewal_term_months": 12})
    _record(f"DNSRegistration {zone_fqdn} @ {spec['registrar']}", created)
    _, created = NSRecord.objects.get_or_create(name="@", server=f"ns1.{zone_fqdn}.", zone=forward_zone)
    _record(f"NSRecord @ -> ns1.{zone_fqdn}.", created)
    _, created = ARecord.objects.get_or_create(name="www", ip_address=ip_www_v4, zone=forward_zone)
    _record(f"ARecord www -> {ip_www_v4.host}", created)
    _, created = ARecord.objects.get_or_create(name="app", ip_address=ip_app_v4, zone=forward_zone)
    _record(f"ARecord app -> {ip_app_v4.host}", created)
    _, created = AAAARecord.objects.get_or_create(name="www", ip_address=ip_www_v6, zone=forward_zone)
    _record(f"AAAARecord www -> {ip_www_v6.host}", created)
    _, created = CNAMERecord.objects.get_or_create(name="docs", alias=f"www.{zone_fqdn}", zone=forward_zone)
    _record(f"CNAMERecord docs -> www.{zone_fqdn}", created)
    _, created = MXRecord.objects.get_or_create(name="@", mail_server=f"mail.{zone_fqdn}", zone=forward_zone, defaults={"preference": 10})
    _record(f"MXRecord @ -> mail.{zone_fqdn} (pref 10)", created)
    _, created = TXTRecord.objects.get_or_create(name="@", text=f"v=spf1 include:_spf.{zone_fqdn} ~all", zone=forward_zone)
    _record("TXTRecord @ (SPF)", created)
    _, created = SRVRecord.objects.get_or_create(name="_sip._tcp", target=f"sip.{zone_fqdn}", port=5060, zone=forward_zone, defaults={"priority": 10, "weight": 5})
    _record(f"SRVRecord _sip._tcp -> sip.{zone_fqdn}:5060", created)
    _, created = PTRRecord.objects.get_or_create(name="10", ptrdname=f"www.{zone_fqdn}", zone=reverse_zone)
    _record(f"PTRRecord 10 -> www.{zone_fqdn}", created)


# Each spec produces an identical count of related objects, all values unique per zone.
SPECS = [
    {"zone": "example.com", "view": "Corporate", "view_desc": "Corporate DNS view.", "registrar": "Example Registrar Inc.", "reg_url": "https://registrar.example.net", "reg_acct": "ACCT-000123", "prefix_v4": "10.10.0.0/24", "prefix_v6": "2001:db8:abcd:12::/64", "reverse_zone": "0.10.10.in-addr.arpa", "ip_www_v4": "10.10.0.10/32", "ip_app_v4": "10.10.0.20/32", "ip_www_v6": "2001:db8:abcd:12::10/128", "expiration": date(2027, 1, 1)},
    {"zone": "example.net", "view": "Marketing", "view_desc": "Marketing DNS view.", "registrar": "NetNames LLC", "reg_url": "https://netnames.example", "reg_acct": "ACCT-000456", "prefix_v4": "10.20.0.0/24", "prefix_v6": "2001:db8:abcd:22::/64", "reverse_zone": "0.20.10.in-addr.arpa", "ip_www_v4": "10.20.0.10/32", "ip_app_v4": "10.20.0.20/32", "ip_www_v6": "2001:db8:abcd:22::10/128", "expiration": date(2028, 4, 15)},
    {"zone": "acme.org", "view": "Engineering", "view_desc": "Engineering DNS view.", "registrar": "Acme Domains Co.", "reg_url": "https://domains.acme.example", "reg_acct": "ACCT-000789", "prefix_v4": "10.30.0.0/24", "prefix_v6": "2001:db8:abcd:32::/64", "reverse_zone": "0.30.10.in-addr.arpa", "ip_www_v4": "10.30.0.10/32", "ip_app_v4": "10.30.0.20/32", "ip_www_v6": "2001:db8:abcd:32::10/128", "expiration": date(2029, 7, 30)},
    {"zone": "contoso.io", "view": "Operations", "view_desc": "Operations DNS view.", "registrar": "Contoso Registrations", "reg_url": "https://reg.contoso.example", "reg_acct": "ACCT-000012", "prefix_v4": "10.40.0.0/24", "prefix_v6": "2001:db8:abcd:42::/64", "reverse_zone": "0.40.10.in-addr.arpa", "ip_www_v4": "10.40.0.10/32", "ip_app_v4": "10.40.0.20/32", "ip_www_v6": "2001:db8:abcd:42::10/128", "expiration": date(2030, 10, 5)},
]

print("Creating example DNS Models data...\n")

# Core Nautobot prerequisites (shared by all zones).
print("Core prerequisites:")
status = Status.objects.get(name="Active")
namespace = Namespace.objects.get(name="Global")

# A Status can only be assigned to a model whose ContentType is registered with it.
# DNSRegistration uses a StatusField, so register its content type with "Active".
dns_registration_ct = ContentType.objects.get_for_model(DNSRegistration)
ct_added = not status.content_types.filter(pk=dns_registration_ct.pk).exists()
status.content_types.add(dns_registration_ct)
_record('Status "Active" -> DNSRegistration content type', ct_added)

for spec in SPECS:
    build_zone(spec, status, namespace)

# Summary
_total = len(_RESULTS)
_created_count = sum(1 for _, was_created in _RESULTS if was_created)
print(f"\nDone. {_created_count} object(s) created, {_total - _created_count} already existed ({_total} total).")
