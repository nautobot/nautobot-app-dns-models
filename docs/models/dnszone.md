# DNS Zone Model

The DNS zone model is used to represent a distinct DNS zone. It contains the zone name, TTL, and SOA record details.

Domain registration attributes are modeled separately in `DNSRegistration`.

- `name` (string): Unique FQDN of the Zone, w/ TLD. e.g `example.com`.
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
- `parent_zone` (DNSZone, read-only): The nearest ancestor zone in the same DNS View, for example `example.com` for `apps.example.com`. It is set automatically, see [Zone Hierarchy](#zone-hierarchy).

A zone cannot have the same name as a [DNS Forwarding Rule](dnsforwardingrule.md) in the same DNS View.

## Zone Hierarchy

`parent_zone` points to the zone in the same DNS View with the longest name that is an ancestor of this zone's name. Names are compared ignoring case. A zone in another DNS View is never a parent, so each view of a split-horizon setup has its own tree.

The hierarchy is kept up to date automatically:

- Creating `b.example.com` between `example.com` and `a.b.example.com` moves `a.b.example.com` under the new zone.
- Renaming a zone, or moving it to another DNS View, recomputes its own parent and the parents of the zones around it.
- Deleting a zone moves its children up to the nearest remaining ancestor.

The zone detail page lists the direct children in a **Child Zones** panel, and the zone list can be filtered by parent zone.

## Delegation

A delegation hands part of a zone's name space over to other name servers. This app does not store delegations as separate objects. It recognizes them from the records in the parent zone, the same way DNS does:

- **Delegation point**: the [NS records](nsrecord.md) at a name other than the zone apex, for example NS records named `apps` in `example.com`.
- **Child zone**: if a zone named `apps.example.com` exists in the same DNS View, the delegation is internal and links to that zone. Otherwise it is external, for example a subdomain run by a mail provider or another team's DNS servers.
- **Glue**: A and AAAA records in the parent zone for name servers that sit at or below the delegated name, for example `ns1.apps` for the name server `ns1.apps.example.com`. Resolvers can only reach such name servers through glue. Name servers outside the delegated name need no glue.

Record names are read relative to their zone. The apex is `@` or the zone name itself, and a name that already ends with the zone name (`apps.example.com` in `example.com`) is treated as zone-qualified.

The following records in `example.com` describe one internal and one external delegation:

| Name | Type | Value | Meaning |
| --- | --- | --- | --- |
| `@` | NS | `ns1.example.com` | Authoritative name server of `example.com`. Not a delegation. |
| `apps` | NS | `ns1.apps.example.com` | Delegates `apps.example.com`. Internal if that zone exists in the same view. |
| `ns1.apps` | A | `192.0.2.53` | Glue for `ns1.apps.example.com`. |
| `mail` | NS | `ns1.mailvendor.net` | Delegates `mail.example.com` to a provider. External, no glue needed. |

### Delegation Panels and Checks

The zone detail page shows:

- **Delegations**: each delegated name with its name servers, glue records, and child zone, or "External".
- **Parent Delegation**: on a zone that has a parent, whether the parent delegates it and with which name servers.
- **Delegation Checks**: problems with the delegations this zone makes or receives. The panel is only shown when there is something to report.

The delegation checks report:

- A child zone in Nautobot that the parent zone has no NS records for, so it is not delegated. A child zone below another delegated name is not reported, because that delegation belongs in a zone Nautobot does not model.
- A delegation whose NS records do not match the apex NS records of the child zone.
- A name server at or below the delegated name that has no glue record in the parent zone.
- Records in the parent zone at or below a delegation point, other than the delegation's NS records and glue. Resolvers never see them, because the child zone answers for those names.

These are warnings only. They never block saving, because a delegation is built from several records that are created one at a time. This app does not create or update delegation records automatically.

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
