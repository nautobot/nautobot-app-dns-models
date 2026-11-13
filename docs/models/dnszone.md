# DNS Zone Model

The DNS zone model is used to represent a distinct DNS zone. It contains the zone name, TTL, and SOA record details.

Domain registration attributes are modeled separately in `DNSRegistration`.

- `name` (string): FQDN of the Zone, w/ TLD. e.g `example.com`. Must be unique within its DNS view, ignoring letter case. See [Zone Name Uniqueness](#zone-name-uniqueness).
- `parent` (DNSZone, read-only): The most specific zone in the same DNS view that encloses this zone. It is set automatically; see [Zone hierarchy](#zone-hierarchy).
- `enabled` (boolean, default `True`): Indicates whether the zone is eligible for publication by external integrations. This app does not publish zones or enforce this setting. The same field exists on every [DNS record](dnsrecord.md) type; disabling a zone does not change the records it contains.
- `ttl` (integer): Time to live for the DNS zone.
- `filename` (string): Filename of the DNS zone file.
- `description`: (string): Description of the DNS zone.
- `soa_mname`: (string): FQDN of the authoritative name server for the DNS zone.
- `soa_rname`: (string): Mailbox or single-label placeholder for the person responsible for the DNS zone.
- `soa_refresh`: (integer): Time in seconds for secondary name servers to query the primary for the SOA record.
- `soa_retry`: (integer): Time in seconds for secondary name servers to retry to request the serial number from the primary.
- `soa_expire`: (integer): Time in seconds for secondary name servers to stop answering requests if the primary does not respond. This value must be bigger than the sum of refresh and retry.
- `soa_serial`: (integer): Serial number of the zone. This value must be incremented each time the zone is changed, and secondary DNS servers must be able to retrieve this value to check if the zone has been updated.
- `soa_minimum`: (integer): Minimum TTL for records in this zone.
- `tenant` (Tenant, optional): Reference to the Tenant model for multi-tenancy support.
- `auto_create_ptr` (boolean, default `False`): When enabled, creating an A or AAAA record in this zone automatically creates a matching PTR record in the most-specific reverse zone within the same DNS view. If no matching reverse zone exists, the A/AAAA creation fails with a validation error.

## Zone Name Uniqueness

DNS names that differ only by letter case are the same name ([RFC 1035 §2.3.3](https://www.rfc-editor.org/rfc/rfc1035.html#section-2.3.3), [RFC 4343 §2](https://www.rfc-editor.org/rfc/rfc4343.html#section-2)). A DNS view therefore cannot contain two zones whose names differ only by case, such as `Example.com` and `example.com`. The same name may exist in different DNS views.

The name is stored with the letter case as entered. Creating or renaming a zone so that it collides with another zone in the same view is rejected with a validation error on `name` in the UI and the REST API, and by the database for any other write path. A zone may change the letter case of its own name.

## Zone hierarchy

Each zone's `parent` is the most specific other zone in the same [DNS view](dnsview.md) whose name is above it in the DNS tree ([RFC 1034 §4.2](https://www.rfc-editor.org/rfc/rfc1034.html#section-4.2)). For example, with zones `com`, `example.com` and `apps.example.com`, the parent of `apps.example.com` is `example.com`, and the parent of `example.com` is `com`. Reverse zones follow the same rule: `1.168.192.in-addr.arpa` is a child of `168.192.in-addr.arpa`.

The parent is derived from zone names and cannot be edited: it is the *closest encloser* ([RFC 9499](https://www.rfc-editor.org/rfc/rfc9499.html)), the longest existing ancestor of the zone's name, among the zones in Nautobot. Names are compared ignoring letter case ([RFC 4343](https://www.rfc-editor.org/rfc/rfc4343.html)), as zone name uniqueness does. Zones in different DNS views are never related.

!!! note
    In RFC terms, a *parent zone* is the zone that delegates a *child zone*. This field does not imply delegation: when a zone in between exists only outside Nautobot, the closest encloser in Nautobot is not the zone that delegates this one.

Zones can be created in any order, and the hierarchy is kept current as zones change:

| Change | Effect |
| --- | --- |
| A zone is created with no enclosing zone | Its parent is empty. |
| A zone is created above existing zones | It becomes the parent of those zones, unless they already have a more specific parent. |
| A zone is created between two existing zones | Zones below it move under it. |
| A zone is deleted | Its children move to the deleted zone's own parent, or have no parent. |
| A zone is renamed or moved to another DNS view | Its parent is recomputed, zones no longer below it move to their new enclosing zone, and zones now below it move under it. |

The zone detail page lists child zones, and the zone list can be filtered by `parent`, `has_parent` and `has_children`.

Each time a zone is saved or deleted, the parents of all zones in its DNS view are recomputed, so the cost of saving a zone grows with the number of zones in the view. Writes that bypass model saves, such as `QuerySet.update()`, `bulk_create()` or direct SQL, do not update parents; the next zone save in the same view repairs them, or run `nautobot-server rebuild_dns_zone_hierarchy` to recompute every view at once.

## SOA RNAME Formats

An SOA RNAME may be entered as an email address, a basic DNS-style mailbox, or a single-label placeholder. Email-style values must be valid email addresses. Basic DNS-style mailboxes are normalized to email form prior to being saved, and single-label placeholders are stored without a trailing dot.

DNS-style mailbox decoding follows [RFC 1035 §3.3.13](https://www.rfc-editor.org/rfc/rfc1035.html#section-3.3.13)
and [§8](https://www.rfc-editor.org/rfc/rfc1035.html#section-8). This app stores decoded mailbox values in
email form as follows:

| Input | Stored value | Result |
| --- | --- | --- |
| `admin@example.com` | `admin@example.com` | Accepted unchanged |
| `admin.example.com.` | `admin@example.com` | Normalized from DNS style |
| `john\.smith.example.com.` | `john.smith@example.com` | The `\.` escape becomes a dot in the mailbox name per [RFC 1035 §5.1](https://www.rfc-editor.org/rfc/rfc1035.html#section-5.1) |
| `invalid.` | `invalid` | Single-label placeholder normalized |
| `john@example` | — | Rejected because the email domain is not fully qualified |
| `admin\046example.com.` | — | Rejected because the DNS escape is unsupported |
| `admin..example.com` | — | Rejected because the DNS-style mailbox is malformed |

+++ 1.2.0 "DNS label length rules"

    When DNS validation is enabled (via the `DNS_VALIDATION_LEVEL` configuration), `DNSZone` enforces the following DNS label length rules, as specified by [RFC 1035 §3.1](https://datatracker.ietf.org/doc/html/rfc1035#section-3.1):

    - Each label (the parts of the name separated by dots) must be no more than 63 bytes in wire format
    - Empty labels (e.g., consecutive dots or leading/trailing dots) are not allowed

    See the [installation guide](../admin/install.md#app-configuration) for configuration options.
