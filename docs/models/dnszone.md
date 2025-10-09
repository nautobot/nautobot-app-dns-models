# DNS Zone Model

The DNS zone model is used to represent a distinct DNS zone. It contains the zone name, TTL, and SOA record details.

- `name` (string): Unique FQDN of the Zone, w/ TLD. e.g `example.com`.
- `ttl` (integer): Time to live for the DNS zone.
- `filename` (string): Filename of the DNS zone file.
- `description`: (string): Description of the DNS zone.
- `soa_mname`: (string): FQDN of the authoritative name server for the DNS zone.
- `soa_rname`: (string): Email address of the administrator for the DNS zone.
- `soa_refresh`: (integer): Time in seconds for secondary name servers to query the master for the SOA record.
- `soa_retry`: (integer): Time in seconds for secondary name servers to retry to request the serial number from the master.
- `soa_expire`: (integer): Time in seconds for secondary name servers to stop answering requests if the master does not respond. This value must be bigger than the sum of refresh and retry.
- `soa_serial`: (integer): Serial number of the zone. This value must be incremented each time the zone is changed, and secondary DNS servers must be able to retrieve this value to check if the zone has been updated.
- `soa_minimum`: (integer): Minimum TTL for records in this zone.

+++ 1.2.0 "DNS label length rules"

    When DNS validation is enabled (via the `DNS_VALIDATION_LEVEL` configuration), `DNSZone` enforces the following DNS label length rules, as specified by [RFC 1035 §3.1](https://datatracker.ietf.org/doc/html/rfc1035#section-3.1):

    - Each label (the parts of the name separated by dots) must be no more than 63 bytes in wire format
    - Empty labels (e.g., consecutive dots or leading/trailing dots) are not allowed

    See the [installation guide](../admin/install.md#app-configuration) for configuration options.
