# TXT Record Model

The TXT Record model represents a Text record in DNS. It associates arbitrary text data with a name and is commonly used for SPF, DKIM, DMARC, and domain verification records.

- `name` (string): FQDN of the record, without TLD.
- `zone` (DNSZoneModel): The DNS zone this record belongs to.
- `ttl` (integer): Time to live for the record.
- `description` (string): Description of the record.
- `comment` (string): Comment for the record.
- `enabled` (boolean, default `True`): Indicates whether the record is eligible for publication by external integrations. This app does not publish records or enforce this setting.
- `text` (string): Text content of the TXT record. See [TXT record content](#txt-record-content) below for the length rules.

## TXT Record Content

+++ 2.4.0 "TXT content length rules"

    `text` previously accepted at most 256 characters, which rejected valid records such as 2048-bit DKIM keys. It now follows the limits defined by [RFC 1035 §3.3.14](https://datatracker.ietf.org/doc/html/rfc1035#section-3.3.14).

TXT record data on the wire is *one or more* `<character-string>` values. Each one is limited to 255 bytes ([RFC 1035 §3.3](https://datatracker.ietf.org/doc/html/rfc1035#section-3.3)), and the record's total data is limited to 65535 bytes by the 16-bit `RDLENGTH` field.

Both limits are counted in **bytes (octets)**, not characters, so a value using non-ASCII characters reaches the limit sooner than its visible length suggests.

### Plain values

A plain value is treated as a single logical string and split into 255-byte `<character-string>` values automatically. A 600-character DKIM key becomes three character-strings (255, 255, and 90 bytes) without any action on your part:

```no-highlight
v=DKIM1; k=rsa; p=MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8A…
```

Splitting never breaks a multi-byte character across two character-strings.

### Explicit character-strings

To control where the boundaries fall, write the value in DNS presentation format: whitespace-separated, double-quoted strings, as you would in a zone file.

```no-highlight
"v=spf1 include:_spf.example.com" "~all"
```

A value that begins with a double quote is parsed this way in full. Escape sequences from [RFC 1035 §5.1](https://datatracker.ietf.org/doc/html/rfc1035#section-5.1) are recognized — `\"`, `\\`, and decimal escapes such as `\065` — and are counted as the single byte they represent. Each quoted string must be 255 bytes or fewer; the app will not split a string you have quoted explicitly.

Mixing quoted and unquoted text in one value is not supported.

### Reading the wire-format strings

The `character_strings` property returns the list of `<character-string>` values a record represents, whichever style was used to enter it. Each value is `bytes`: the exact octets sent on the wire, with escapes decoded, so `\200` is the single octet 200. Integrations that publish these records should use it rather than splitting `text` themselves.

### Enforcement

Like the DNS name checks, these rules follow the `DNS_VALIDATION_LEVEL` setting (see the [installation guide](../admin/install.md#app-configuration)):

- **Wire format** (default) — a TXT record that breaks the rules, or whose quoted value cannot be parsed, is rejected when it is created or edited.
- **Disabled** — no TXT content checks run, and the value is saved as entered. If a saved value begins with a double quote but is not valid presentation format, reading `character_strings` raises a `ValidationError`.

## Uniqueness

A TXT record is unique on `name`, `zone`, and `text`. Because `text` is now unbounded, the database constraint is applied to a SHA-256 digest of `text` rather than to the column itself — MySQL cannot index a `TEXT` column without a prefix length. This is an internal implementation detail: the digest is not exposed through the REST API, filters, or forms, and the record's natural key remains `name`, `text`, and `zone`.
