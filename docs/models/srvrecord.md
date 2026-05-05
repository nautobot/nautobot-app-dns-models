# SRV Record Model

The SRV Record model represents a Service record in DNS. SRV records identify the host and port for specific services (e.g. SIP, XMPP), with priority and weight values used to order multiple targets and distribute load.

- `name` (string): FQDN of the record, without TLD.
- `zone` (DNSZoneModel): The DNS zone this record belongs to.
- `ttl` (integer): Time to live for the record.
- `description` (string): Description of the record.
- `comment` (string): Comment for the record.
- `priority` (integer): Priority of the SRV record. Lower values are preferred. Range 0–65535, default 0.
- `weight` (integer): Relative weight for records with the same priority. Range 0–65535, default 0.
- `port` (integer): Port number of the service. Range 0–65535.
- `target` (string): FQDN of the target host providing the service.
