# DNS Record Model

`DNSRecord` is the abstract base model shared by every record type (A, AAAA, CNAME, MX, NS, PTR, SRV, and TXT). The fields below are available on all of them:

- `name` (string): FQDN of the record, without TLD.
- `zone` (DNSZone): The DNS zone this record belongs to.
- `ttl` (integer): Time to live for the record. If unset, the zone TTL is used.
- `enabled` (boolean, default `True`): Indicates whether the record is eligible for publication by external integrations. This app does not publish records or enforce this setting.
- `description` (string): Description of the record.
- `comment` (string): Comment for the record.

`enabled` is defined on `DNSModel`, so it is available on both [DNS Zone](dnszone.md) and every record type. The flags are independent: disabling a zone does not change the `enabled` value of the records it contains, and consumers of the data are responsible for deciding how to combine them.

+++ 1.2.0 "DNS name length rules"

    When DNS validation is enabled (via the `DNS_VALIDATION_LEVEL` configuration), `DNSRecord` enforces the following DNS label and name length rules, as specified by [RFC 1035 §3.1](https://datatracker.ietf.org/doc/html/rfc1035#section-3.1):

    - Each label (the parts of the name separated by dots) must be no more than 63 bytes in wire format
    - Empty labels (e.g., consecutive dots or leading/trailing dots) are not allowed
    - The total length of the fully qualified DNS name (including the zone and all dots, in wire format) must not exceed 255 bytes

    See the [installation guide](../admin/install.md#app-configuration) for configuration options.