# A Record Model

The A Record model is used to represent IPv4 address records in DNS. It maps a hostname to an IPv4 address.

- `name` (string): FQDN of the record, without TLD.
- `zone` (DNSZoneModel): The DNS zone this record belongs to.
- `ttl` (integer): Time to live for the record.
- `description` (string): Description of the record.
- `comment` (string): Comment for the record.
- `ip_address` (IPAddress): IPv4 address for the record (A records must use IPv4).

+++ 2.0.0
    `address` field in A Record is now `ip_address`
