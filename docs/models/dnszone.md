# DNS Zone Model

The DNS zone model is used to represent a distinct DNS zone. It contains the zone name, TTL, and SOA record details.

Domain registration attributes are modeled separately in `DNSRegistration`.

- `name` (string): Unique FQDN of the Zone, w/ TLD. e.g `example.com`.
- `ttl` (integer): Time to live for the DNS zone.
- `filename` (string): Filename of the DNS zone file.
- `description`: (string): Description of the DNS zone.
- `soa_mname`: (string): FQDN of the authoritative name server for the DNS zone.
- `soa_rname`: (string): Email address of the administrator for the DNS zone.
- `soa_refresh`: (integer): Time in seconds for secondary name servers to query the master for the SOA record.
- `soa_retry`: (integer): Time in seconds for secondary name servers to retry to request the serial number from the master.
- `soa_expire`: (integer): Time in seconds for secondary name servers to stop answering requests if the master does not respond. This value must be bigger than the sum of refresh and retry.
- `soa_serial`: (integer): Serial number of the zone (0–2,147,483,647). This value must be incremented each time the zone is changed, and secondary DNS servers must be able to retrieve this value to check if the zone has been updated. See [SOA Serial Auto-Increment](#soa-serial-auto-increment) below.
- `soa_minimum`: (integer): Minimum TTL for records in this zone.
- `tenant` (Tenant, optional): Reference to the Tenant model for multi-tenancy support.

+++ 1.2.0 "DNS label length rules"

    When DNS validation is enabled (via the `DNS_VALIDATION_LEVEL` configuration), `DNSZone` enforces the following DNS label length rules, as specified by [RFC 1035 §3.1](https://datatracker.ietf.org/doc/html/rfc1035#section-3.1):

    - Each label (the parts of the name separated by dots) must be no more than 63 bytes in wire format
    - Empty labels (e.g., consecutive dots or leading/trailing dots) are not allowed

    See the [installation guide](../admin/install.md#app-configuration) for configuration options.

+++ 2.1.0 "SOA serial auto-increment"

    ## SOA Serial Auto-Increment

    When enabled via the `SOA_SERIAL_AUTO_INCREMENT` [configuration option](../admin/install.md#app-configuration), the `soa_serial` field is automatically incremented by 1 whenever zone data changes. This includes:

    - **Record changes** — Creating, updating, or deleting any record type (A, AAAA, PTR, CNAME, NS, MX, SRV, TXT) in the zone.
    - **Zone self-changes** — Modifying zone fields such as `name`, `ttl`, `filename`, `soa_mname`, `soa_rname`, `soa_refresh`, `soa_retry`, `soa_expire`, or `soa_minimum`.

    Changes to `description` or `tenant` do **not** trigger a serial increment, as these fields are not part of the DNS zone data served to secondary name servers.

    The `soa_serial` field is a Django `IntegerField` with a valid range of 0–2,147,483,647 for user-supplied values in both the GUI and API. The auto-increment wraps around to 0 when the serial reaches its maximum value, consistent with [RFC 1982 (Serial Number Arithmetic)](https://datatracker.ietf.org/doc/html/rfc1982).

    !!! note
        `QuerySet.bulk_create()` does not trigger auto-increment because Django does not fire `post_save` signals for bulk-created objects. Use individual `.save()` calls or the REST API for operations that require serial tracking.
