"""Generate test data for the Nautobot DNS Models app."""

from datetime import date

from django.contrib.contenttypes.models import ContentType
from django.core.management.base import BaseCommand, CommandError
from django.db import DEFAULT_DB_ALIAS, transaction
from nautobot.extras.models import Status
from nautobot.ipam.models import IPAddress, Namespace, Prefix
from nautobot.tenancy.models import Tenant

from nautobot_dns_models.choices import DNSForwardingRuleActionChoices
from nautobot_dns_models.models import (
    AAAARecord,
    ARecord,
    CNAMERecord,
    DNSForwardingRule,
    DNSForwardingRuleIPAddressAssignment,
    DNSRegistrar,
    DNSRegistration,
    DNSView,
    DNSViewPrefixAssignment,
    DNSZone,
    MXRecord,
    NSRecord,
    PTRRecord,
    SRVRecord,
    TXTRecord,
    get_default_view_pk,
)

INTERNAL_VIEW = "Internal"
DEFAULT_VIEW = "Default"
REGISTRAR = "Example Registrar"
TENANT = "Example Corp"

PREFIXES = (
    "10.0.0.0/8",
    "192.0.2.0/24",
    "198.51.100.0/24",
    "2001:db8::/32",
    "8.8.8.0/24",
    "8.8.4.0/24",
)

# (view, zone name, SOA MNAME)
ZONES = (
    (DEFAULT_VIEW, "example.com", "ns1.example.com"),
    (DEFAULT_VIEW, "apps.example.com", "ns1.apps.example.com"),
    (DEFAULT_VIEW, "lab.example.com", "ns1.example.com"),
    (DEFAULT_VIEW, "2.0.192.in-addr.arpa", "ns1.example.com"),
    (INTERNAL_VIEW, "example.com", "ns-int1.example.com"),
)

# (view, zone, record name, server)
NS_RECORDS = (
    (DEFAULT_VIEW, "example.com", "@", "ns1.example.com"),
    (DEFAULT_VIEW, "example.com", "@", "ns2.example.com"),
    # Internal delegation: the child zone is modeled in Nautobot.
    (DEFAULT_VIEW, "example.com", "apps", "ns1.apps.example.com"),
    (DEFAULT_VIEW, "example.com", "apps", "ns2.apps.example.com"),
    # External delegation: a mail provider runs the child zone.
    (DEFAULT_VIEW, "example.com", "mail", "ns1.mailvendor.net"),
    (DEFAULT_VIEW, "example.com", "mail", "ns2.mailvendor.net"),
    (DEFAULT_VIEW, "apps.example.com", "@", "ns1.apps.example.com"),
    (DEFAULT_VIEW, "apps.example.com", "@", "ns2.apps.example.com"),
    # lab.example.com is deliberately not delegated from example.com, to demonstrate the delegation checks.
    (DEFAULT_VIEW, "lab.example.com", "@", "ns1.example.com"),
    (DEFAULT_VIEW, "2.0.192.in-addr.arpa", "@", "ns1.example.com"),
    (INTERNAL_VIEW, "example.com", "@", "ns-int1.example.com"),
    (INTERNAL_VIEW, "example.com", "@", "ns-int2.example.com"),
    # Active Directory domain served by Microsoft DNS on the domain controllers.
    (INTERNAL_VIEW, "example.com", "ad", "dc1.ad.example.com"),
    (INTERNAL_VIEW, "example.com", "ad", "dc2.ad.example.com"),
)

# (view, zone, record name, address)
ADDRESS_RECORDS = (
    (DEFAULT_VIEW, "example.com", "ns1", "192.0.2.1/32"),
    (DEFAULT_VIEW, "example.com", "ns2", "192.0.2.2/32"),
    (DEFAULT_VIEW, "example.com", "www", "192.0.2.10/32"),
    (DEFAULT_VIEW, "example.com", "www", "2001:db8::10/128"),
    # Glue for the apps delegation.
    (DEFAULT_VIEW, "example.com", "ns1.apps", "192.0.2.53/32"),
    (DEFAULT_VIEW, "example.com", "ns2.apps", "192.0.2.54/32"),
    # Deliberately hidden by the mail delegation, to demonstrate the delegation checks.
    (DEFAULT_VIEW, "example.com", "legacy.mail", "192.0.2.99/32"),
    (DEFAULT_VIEW, "apps.example.com", "ns1", "192.0.2.53/32"),
    (DEFAULT_VIEW, "apps.example.com", "ns2", "192.0.2.54/32"),
    (DEFAULT_VIEW, "apps.example.com", "portal", "192.0.2.60/32"),
    (DEFAULT_VIEW, "apps.example.com", "api", "192.0.2.61/32"),
    (DEFAULT_VIEW, "lab.example.com", "bench", "192.0.2.70/32"),
    (INTERNAL_VIEW, "example.com", "ns-int1", "10.0.0.53/32"),
    (INTERNAL_VIEW, "example.com", "ns-int2", "10.0.0.54/32"),
    (INTERNAL_VIEW, "example.com", "intranet", "10.0.1.10/32"),
    (INTERNAL_VIEW, "example.com", "dc1.ad", "10.0.10.11/32"),
    (INTERNAL_VIEW, "example.com", "dc2.ad", "10.0.10.12/32"),
)

# (view, name, action, description, [(address, port, weight)])
FORWARDING_RULES = (
    (
        INTERNAL_VIEW,
        ".",
        DNSForwardingRuleActionChoices.ACTION_FORWARD_FIRST,
        "Global forwarders for everything the internal resolvers are not authoritative for.",
        [("8.8.8.8/32", 53, 10), ("8.8.4.4/32", 53, 20)],
    ),
    (
        INTERNAL_VIEW,
        "ad.example.com",
        DNSForwardingRuleActionChoices.ACTION_FORWARD_ONLY,
        "Conditional forwarder to the Active Directory domain controllers.",
        [("10.0.10.11/32", 53, 10), ("10.0.10.12/32", 53, 20)],
    ),
    (
        INTERNAL_VIEW,
        "partner.example.net",
        DNSForwardingRuleActionChoices.ACTION_FORWARD_FIRST,
        "Partner resolvers over the site-to-site VPN. The second one listens on a non-standard port.",
        [("198.51.100.53/32", 53, 10), ("198.51.100.54/32", 5353, 20)],
    ),
    (
        INTERNAL_VIEW,
        "public.partner.example.net",
        DNSForwardingRuleActionChoices.ACTION_DO_NOT_FORWARD,
        "Exemption: the partner's public names resolve normally instead of through the VPN.",
        [],
    ),
    (
        INTERNAL_VIEW,
        "cloud.example.com",
        DNSForwardingRuleActionChoices.ACTION_FORWARD_ONLY,
        "Cloud resolver inbound endpoint. Deliberately not delegated in example.com, to demonstrate the rule checks.",
        [("10.0.20.2/32", 53, 10)],
    ),
)


class Command(BaseCommand):
    """Populate the database with various data as a baseline for testing (automated or manual)."""

    help = __doc__

    def __init__(self, *args, **kwargs):
        """Declare the IPAM and tenancy objects shared by the generation steps."""
        super().__init__(*args, **kwargs)
        self.namespace = None
        self.active = None
        self.tenant = None

    def add_arguments(self, parser):
        """Add command line arguments."""
        parser.add_argument(
            "--database",
            default=DEFAULT_DB_ALIAS,
            help='The database to generate the test data in. Defaults to the "default" database.',
        )
        parser.add_argument(
            "--flush",
            action="store_true",
            help="Flush any existing Nautobot DNS Models test data from the database before generating new data.",
        )

    @staticmethod
    def _get_or_create(model, defaults=None, **lookup):
        """Return the object matching `lookup`, creating it with `validated_save()` if it does not exist."""
        instance = model.objects.filter(**lookup).first()
        if instance is None:
            instance = model(**lookup, **(defaults or {}))
            instance.validated_save()
        return instance

    def _generate_static_data(self):
        """Generate static data required for test cases."""
        self.namespace = Namespace.objects.get(name="Global")
        self.active = Status.objects.get(name="Active")
        self.tenant = self._get_or_create(Tenant, name=TENANT)
        for prefix in PREFIXES:
            self._get_or_create(Prefix, prefix=prefix, namespace=self.namespace, defaults={"status": self.active})

        views = self._generate_views()
        zones = self._generate_zones(views)
        self._generate_records(zones)
        self._generate_registration(zones[(DEFAULT_VIEW, "example.com")])
        self._generate_forwarding_rules(views)

    def _ip_address(self, address):
        """Return the IP address in the Global namespace, creating it if needed."""
        host, mask_length = address.split("/")
        ip = IPAddress.objects.filter(host=host, mask_length=int(mask_length), parent__namespace=self.namespace).first()
        if ip is None:
            ip = IPAddress(address=address, namespace=self.namespace, status=self.active)
            ip.validated_save()
        return ip

    def _generate_views(self):
        """Return the demo DNS Views keyed by name."""
        internal_view = self._get_or_create(
            DNSView, name=INTERNAL_VIEW, defaults={"description": "Split-horizon view for internal clients."}
        )
        internal_prefix = Prefix.objects.get(prefix="10.0.0.0/8", namespace=self.namespace)
        self._get_or_create(DNSViewPrefixAssignment, dns_view=internal_view, prefix=internal_prefix)
        return {DEFAULT_VIEW: DNSView.objects.get(pk=get_default_view_pk()), INTERNAL_VIEW: internal_view}

    def _generate_zones(self, views):
        """Return the demo zones keyed by (view name, zone name)."""
        return {
            (view_name, zone_name): self._get_or_create(
                DNSZone,
                name=zone_name,
                dns_view=views[view_name],
                defaults={
                    "filename": f"{zone_name}.zone",
                    "soa_mname": mname,
                    "soa_rname": "hostmaster@example.com",
                    "tenant": self.tenant,
                },
            )
            for view_name, zone_name, mname in ZONES
        }

    def _generate_records(self, zones):
        """Generate the demo records of every type."""
        for view_name, zone_name, name, server in NS_RECORDS:
            self._get_or_create(NSRecord, zone=zones[(view_name, zone_name)], name=name, server=server)

        for view_name, zone_name, name, address in ADDRESS_RECORDS:
            ip = self._ip_address(address)
            model = ARecord if ip.ip_version == 4 else AAAARecord
            self._get_or_create(model, zone=zones[(view_name, zone_name)], name=name, ip_address=ip)

        public_zone = zones[(DEFAULT_VIEW, "example.com")]
        self._get_or_create(CNAMERecord, zone=public_zone, name="blog", alias="www.example.com")
        self._get_or_create(
            MXRecord, zone=public_zone, name="@", mail_server="mx1.mailvendor.net", defaults={"preference": 10}
        )
        self._get_or_create(TXTRecord, zone=public_zone, name="@", text="v=spf1 include:mailvendor.net -all")
        self._get_or_create(
            SRVRecord,
            zone=public_zone,
            name="_sip._tcp",
            target="www.example.com",
            port=5060,
            defaults={"priority": 10, "weight": 60},
        )
        reverse_zone = zones[(DEFAULT_VIEW, "2.0.192.in-addr.arpa")]
        for name, ptrdname in (("1", "ns1.example.com"), ("2", "ns2.example.com"), ("10", "www.example.com")):
            self._get_or_create(PTRRecord, zone=reverse_zone, name=name, ptrdname=ptrdname)

    def _generate_registration(self, zone):
        """Generate the demo registrar and the registration of `zone`."""
        registrar = self._get_or_create(
            DNSRegistrar, name=REGISTRAR, defaults={"url": "https://registrar.example.net", "account_number": "EX-1001"}
        )
        self.active.content_types.add(ContentType.objects.get_for_model(DNSRegistration))
        self._get_or_create(
            DNSRegistration,
            dns_registrar=registrar,
            dns_zone=zone,
            defaults={"status": self.active, "expiration_date": date(2027, 10, 21), "auto_renewal": True},
        )

    def _generate_forwarding_rules(self, views):
        """Generate the demo forwarding rules and their forwarders."""
        for view_name, name, action, description, forwarders in FORWARDING_RULES:
            rule = self._get_or_create(
                DNSForwardingRule,
                name=name,
                dns_view=views[view_name],
                defaults={"action": action, "description": description, "tenant": self.tenant},
            )
            for address, port, weight in forwarders:
                self._get_or_create(
                    DNSForwardingRuleIPAddressAssignment,
                    forwarding_rule=rule,
                    ip_address=self._ip_address(address),
                    port=port,
                    defaults={"weight": weight},
                )

    def _flush_static_data(self):
        """Delete the DNS objects created by `_generate_static_data`. IPAM and tenancy objects are kept."""
        DNSForwardingRule.objects.filter(
            dns_view__name=INTERNAL_VIEW, name__in=[rule[1] for rule in FORWARDING_RULES]
        ).delete()
        zone_filter = {"dns_view__name__in": [DEFAULT_VIEW, INTERNAL_VIEW]}
        demo_zones = DNSZone.objects.filter(name__in={zone[1] for zone in ZONES}, **zone_filter)
        DNSRegistration.objects.filter(dns_zone__in=demo_zones).delete()
        for model in (NSRecord, ARecord, AAAARecord, CNAMERecord, MXRecord, TXTRecord, PTRRecord, SRVRecord):
            model.objects.filter(zone__in=demo_zones).delete()
        demo_zones.delete()
        DNSRegistrar.objects.filter(name=REGISTRAR).delete()
        DNSView.objects.filter(name=INTERNAL_VIEW).delete()

    def handle(self, *args, **options):
        """Entry point to the management command."""
        if options["database"] != DEFAULT_DB_ALIAS:
            raise CommandError("Only the default database is supported.")

        with transaction.atomic():
            if options["flush"]:
                self.stdout.write("Flushing existing Nautobot DNS Models test data...")
                self._flush_static_data()

            self._generate_static_data()

        self.stdout.write(self.style.SUCCESS(f"Database {options['database']} populated with app data successfully!"))
