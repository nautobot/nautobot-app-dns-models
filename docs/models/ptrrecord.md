# PTR Record Model

The PTR Record model represents a Pointer record in DNS. PTR records are used for reverse DNS lookups, mapping an IP address (encoded as a name under `in-addr.arpa` or `ip6.arpa`) to a domain name.

- `name` (string): FQDN of the record, without TLD.
- `zone` (DNSZoneModel): The DNS zone this record belongs to.
- `ttl` (integer): Time to live for the record.
- `description` (string): Description of the record.
- `comment` (string): Comment for the record.
- `ptrdname` (string): Domain name that the record points to.
