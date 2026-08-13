# NS Record Model

The NS Record model represents a Name Server record in DNS. It identifies an authoritative name server for a zone.

- `name` (string): FQDN of the record, without TLD.
- `zone` (DNSZoneModel): The DNS zone this record belongs to.
- `ttl` (integer): Time to live for the record.
- `description` (string): Description of the record.
- `comment` (string): Comment for the record.
- `enabled` (boolean, default `True`): Indicates whether the record is eligible for publication by external integrations. This app does not publish records or enforce this setting.
- `server` (string): FQDN of the authoritative name server.
