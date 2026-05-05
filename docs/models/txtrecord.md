# TXT Record Model

The TXT Record model represents a Text record in DNS. It associates arbitrary text data with a name and is commonly used for SPF, DKIM, DMARC, and domain verification records.

- `name` (string): FQDN of the record, without TLD.
- `zone` (DNSZoneModel): The DNS zone this record belongs to.
- `ttl` (integer): Time to live for the record.
- `description` (string): Description of the record.
- `comment` (string): Comment for the record.
- `text` (string): Text content of the TXT record (max 256 characters).
