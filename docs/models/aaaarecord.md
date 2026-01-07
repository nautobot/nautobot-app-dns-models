# AAAA Record Model

The AAAA Record model is used to represent IPv6 address records in DNS. It maps a hostname to an IPv6 address.

- `name` (string): FQDN of the record, without TLD.
- `zone` (DNSZoneModel): The DNS zone this record belongs to.
- `ttl` (integer): Time to live for the record.
- `description` (string): Description of the record.
- `comment` (string): Comment for the record.
- `ip_address` (IPAddress): IPv6 address for the record (AAAA records must use IPv6).

+++ 2.0.0
    `address` field in AAAA Record is now `ip_address`
