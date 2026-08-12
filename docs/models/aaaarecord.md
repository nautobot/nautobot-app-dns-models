# AAAA Record Model

The AAAA Record model is used to represent IPv6 address records in DNS. It maps a hostname to an IPv6 address.

- `name` (string): FQDN of the record, without TLD.
- `zone` (DNSZoneModel): The DNS zone this record belongs to.
- `ttl` (integer): Time to live for the record.
- `description` (string): Description of the record.
- `comment` (string): Comment for the record.
- `enabled` (boolean, default `True`): Indicates whether the record is eligible for publication by external integrations. This app does not publish records or enforce this setting.
- `ip_address` (IPAddress): IPv6 address for the record (AAAA records must use IPv6).

When the parent `DNSZone` has `auto_create_ptr` enabled, creating an AAAA record automatically creates a matching PTR record in the most-specific reverse zone within the same DNS view. See [DNS Zone](dnszone.md) for details.

+++ 2.0.0
    `address` field in AAAA Record is now `ip_address`
