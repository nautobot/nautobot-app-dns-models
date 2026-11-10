# Frequently Asked Questions

## Does this App turn Nautobot into a DDI Solution?

No, but you now have DNS as well as IPAM data in one place, so you can write your own automation, like Nautobot Jobs, to deploy/verify configuration on your servers!

## DNS Naming Rules and Internationalization

### Why does my internationalized domain name (or label) fail validation even though it looks short enough?
For internationalized names (those containing non-ASCII characters), the DNS protocol uses a special encoding called IDNA (Internationalized Domain Names in Applications). Some characters use more than one byte in this encoding, so a label or name may reach the 63-byte (per label) or 255-byte (full name) limit before it reaches 63 or 255 characters.

!!! tip
    If you see a length error, try using fewer characters or only ASCII letters and digits. The app checks the encoded (wire format) length, not just the visible character count.

---

### What DNS standards does this app follow for name validation?
This app enforces DNS naming rules as specified in:

- **[RFC 1035 §2.3.4](https://datatracker.ietf.org/doc/html/rfc1035#section-2.3.4):**
  Maximum label (63 bytes) and full name (255 bytes) length limits for DNS.

This ensures that all DNS names are valid, interoperable, and compatible with the global DNS system.

!!! note
    DNS validation can be configured or disabled via the `DNS_VALIDATION_LEVEL` setting. See the [installation guide](../admin/install.md#app-configuration) for details.

---

### What does "wire format" mean in the context of DNS names?
"Wire format" refers to the way DNS names are encoded for transmission over the network. Each label is encoded using the IDNA 2003 standard, and the total length (in bytes) of all labels and dots must not exceed 255 bytes. This is stricter than simply counting characters, especially for internationalized names.

---

## TXT Records

### Can I store a 2048-bit DKIM key in a TXT record?
Yes. A TXT record's content is limited to 65535 bytes in total, and the app splits long values into the 255-byte `<character-string>` values that DNS uses on the wire. Paste the key as-is; no manual splitting is required.

!!! note
    Versions before 2.4.0 limited TXT content to 256 characters, which rejected most 2048-bit DKIM keys.

---

### When should I split a TXT value into quoted strings myself?
Only when the boundaries matter to whatever consumes the record. Some SPF and DMARC tooling is sensitive to where a long policy is divided, and a few providers expect the strings exactly as published. In those cases, write the value in DNS presentation format, the same way you would in a zone file:

```no-highlight
"v=spf1 include:_spf.example.com" "~all"
```

Each quoted string must be 255 bytes or fewer — the app will not further split a string you have quoted explicitly. See the [TXT Record model](../models/txtrecord.md#explicit-character-strings) documentation for the full rules.

---

### Why does my TXT record fail validation when it looks shorter than 255 characters?
The limits are counted in bytes, not characters. A non-ASCII character can occupy up to four bytes in UTF-8, so a value with accented characters or emoji reaches 255 bytes well before it reaches 255 characters.
