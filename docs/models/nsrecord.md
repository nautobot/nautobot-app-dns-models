# NS Record Model

The NS Record model represents a Name Server record in DNS. It identifies an authoritative name server for a zone.

- `name` (string): FQDN of the record, without TLD.
- `zone` (DNSZoneModel): The DNS zone this record belongs to.
- `ttl` (integer): Time to live for the record.
- `description` (string): Description of the record.
- `comment` (string): Comment for the record.
- `server` (string): FQDN of the authoritative name server.
