# DNS Record Model

+++ 1.2.0 "DNS name length rules"

When DNS validation is enabled (via the `DNS_VALIDATION_LEVEL` configuration), `DNSRecordModel` enforces the following DNS label and name length rules, as specified by [RFC 1035 §3.1](https://datatracker.ietf.org/doc/html/rfc1035#section-3.1):

- Each label (the parts of the name separated by dots) must be no more than 63 bytes in wire format
- Empty labels (e.g., consecutive dots or leading/trailing dots) are not allowed
- The total length of the fully qualified DNS name (including the zone and all dots, in wire format) must not exceed 255 bytes

See the [installation guide](../admin/install.md#app-configuration) for configuration options.