"""Link existing PTR records to the IP Addresses encoded in their reverse pointer names."""

from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand
from django.db import transaction
from nautobot.ipam.models import IPAddress

from nautobot_dns_models.models import PTRRecord, ptr_record_fqdn, reverse_pointer_to_ip


class Command(BaseCommand):
    """Link PTR records to IP Addresses by parsing each record's reverse pointer name (name + zone).

    By default this is a dry run that only reports the proposed links. Pass --commit to apply them.
    """

    help = __doc__

    def add_arguments(self, parser):
        """Add command line arguments."""
        parser.add_argument(
            "--commit",
            action="store_true",
            help="Apply the proposed links. Without this flag no changes are written.",
        )
        parser.add_argument(
            "--relink",
            action="store_true",
            help="Also evaluate PTR records that are already linked to an IP Address.",
        )
        parser.add_argument(
            "--zone",
            action="append",
            dest="zones",
            default=[],
            metavar="NAME",
            help="Only evaluate PTR records in this reverse zone. May be given more than once.",
        )

    def handle(self, *args, **options):
        """Entry point to the management command."""
        ptr_records = PTRRecord.objects.select_related("zone", "ip_address").order_by("zone__name", "name")
        if not options["relink"]:
            ptr_records = ptr_records.filter(ip_address__isnull=True)
        if options["zones"]:
            ptr_records = ptr_records.filter(zone__name__in=options["zones"])

        links, ambiguous, no_match, unparseable = [], [], [], []
        for ptr_record in ptr_records:
            fqdn = ptr_record_fqdn(ptr_record)
            ip_value = reverse_pointer_to_ip(fqdn)
            if ip_value is None:
                unparseable.append(ptr_record)
                continue

            candidates = list(IPAddress.objects.filter(host=str(ip_value)).select_related("parent__namespace"))
            if not candidates:
                no_match.append((ptr_record, ip_value))
            elif len(candidates) > 1:
                ambiguous.append((ptr_record, candidates))
            elif candidates[0].pk != ptr_record.ip_address_id:
                links.append((ptr_record, candidates[0]))

        self._report(links, ambiguous, no_match, unparseable)

        if not options["commit"]:
            self.stdout.write(self.style.WARNING("Dry run: no changes were made. Re-run with --commit to apply."))
            return

        linked, failed = self._apply(links)
        self.stdout.write(self.style.SUCCESS(f"Linked {linked} PTR record(s)."))
        if failed:
            self.stdout.write(self.style.ERROR(f"Failed to link {failed} PTR record(s); see errors above."))

    def _report(self, links, ambiguous, no_match, unparseable):
        """Write the proposed links and the records that could not be linked."""
        self.stdout.write(f"PTR records to link ({len(links)}):")
        for ptr_record, ip_address in links:
            self.stdout.write(
                f"  {ptr_record_fqdn(ptr_record)} ({ptr_record.ptrdname}) -> {ip_address} "
                f"[{ip_address.parent.namespace}]"
            )

        self.stdout.write(f"Ambiguous, multiple matching IP Addresses ({len(ambiguous)}):")
        for ptr_record, candidates in ambiguous:
            matches = ", ".join(f"{ip_address} [{ip_address.parent.namespace}]" for ip_address in candidates)
            self.stdout.write(f"  {ptr_record_fqdn(ptr_record)} ({ptr_record.ptrdname}) -> {matches}")

        self.stdout.write(f"No matching IP Address ({len(no_match)}):")
        for ptr_record, ip_value in no_match:
            self.stdout.write(f"  {ptr_record_fqdn(ptr_record)} ({ptr_record.ptrdname}) -> {ip_value}")

        self.stdout.write(f"Not a full reverse pointer name ({len(unparseable)}):")
        for ptr_record in unparseable:
            self.stdout.write(f"  {ptr_record_fqdn(ptr_record)} ({ptr_record.ptrdname})")

        self.stdout.write(
            f"Summary: {len(links)} to link, {len(ambiguous)} ambiguous, "
            f"{len(no_match)} without a match, {len(unparseable)} unparseable."
        )

    def _apply(self, links):
        """Save the proposed links, returning the number of successes and failures."""
        linked = failed = 0
        for ptr_record, ip_address in links:
            ptr_record.ip_address = ip_address
            try:
                with transaction.atomic():
                    ptr_record.validated_save()
            except ValidationError as error:
                failed += 1
                self.stdout.write(self.style.ERROR(f"  {ptr_record_fqdn(ptr_record)}: {error}"))
            else:
                linked += 1
        return linked, failed
