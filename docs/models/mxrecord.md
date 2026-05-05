# MX Record Model

The MX Record model represents a Mail Exchanger record in DNS. It specifies a mail server responsible for accepting email for the zone, along with a preference value used to order multiple MX records.

- `name` (string): FQDN of the record, without TLD.
- `zone` (DNSZoneModel): The DNS zone this record belongs to.
- `ttl` (integer): Time to live for the record.
- `description` (string): Description of the record.
- `comment` (string): Comment for the record.
- `preference` (integer): Preference for the MX record. Lower values are preferred. Range 0–65535, default 10.
- `mail_server` (string): FQDN of the mail server.
