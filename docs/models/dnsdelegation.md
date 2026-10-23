# DNS Delegation Model

A DNS delegation marks a zone cut: the owner name in a parent zone below which authority passes to other name servers ([RFC 1034 §4.2.1](https://www.rfc-editor.org/rfc/rfc1034.html#section-4.2.1)). For example, a delegation named `apps` in the zone `example.com` delegates `apps.example.com`.

- `zone` (DNSZone): The parent zone that contains the zone cut.
- `name` (string): The owner name of the zone cut, relative to the zone, e.g. `apps`. An absolute name such as `apps.example.com.` is stored relative to the zone. The zone apex (`@`) cannot be delegated.
- `description` (string): Description of the delegation.

A delegation stores no name server data. Its name servers and glue are ordinary records in the parent zone:

- **NS records:** the [NS records](nsrecord.md) in the parent zone whose `name` equals the delegation's `name`. Names are compared ignoring letter case.
- **Glue:** the [A](arecord.md) and [AAAA](aaaarecord.md) records in the parent zone at a name server's name.

NS records that are not at a delegation's owner name keep their usual meaning and are never treated as delegations.

## Example

```zone
$ORIGIN example.com.
apps      NS  ns1.apps.example.com.   ; in-domain name server
apps      NS  ns2.other.net.          ; out-of-bailiwick name server
ns1.apps  A   192.0.2.10              ; glue
```

| Object | Fields |
| --- | --- |
| DNS Delegation | `zone`: `example.com`, `name`: `apps` |
| NS Record | `zone`: `example.com`, `name`: `apps`, `server`: `ns1.apps.example.com` |
| NS Record | `zone`: `example.com`, `name`: `apps`, `server`: `ns2.other.net` |
| A Record | `zone`: `example.com`, `name`: `ns1.apps`, `ip_address`: `192.0.2.10/32` |

!!! note
    Record names are relative to their zone. Enter the glue record as `ns1.apps`, not `ns1.apps.example.com.`: the record name keeps everything before the trailing dot, so the second form would mean `ns1.apps.example.com.example.com`.

## Name servers and glue

Each name server of a delegation is classified by where its name sits relative to the zone cut, using the terms of [RFC 9499 §7](https://www.rfc-editor.org/rfc/rfc9499.html#section-7):

| Class | Example for `apps.example.com` | Where its addresses come from |
| --- | --- | --- |
| In-domain | `ns1.apps.example.com` | Glue A/AAAA records in the parent zone. These are required, because nothing else can resolve the name ([RFC 9471 §2.1](https://www.rfc-editor.org/rfc/rfc9471.html#section-2.1)). |
| Sibling domain | `ns.example.com` | The parent zone's own A/AAAA records, which also serve as glue ([RFC 9471 §2.2](https://www.rfc-editor.org/rfc/rfc9471.html#section-2.2)). |
| Out-of-bailiwick | `ns2.other.net` | The zone that contains the name. The parent zone does not carry these addresses ([RFC 2181 §5.4.1](https://www.rfc-editor.org/rfc/rfc2181.html#section-5.4.1)). |

The delegation detail page lists each name server with its class and the addresses known in Nautobot. For an out-of-bailiwick name server, the addresses come from the zone in the same DNS view that contains the name, if there is one.

If a zone named after the delegated domain exists in the same DNS view, it is shown as the child zone. See [Zone hierarchy](dnszone.md#zone-hierarchy).

## Data Compliance

The app registers the following [Data Validation Engine](https://docs.nautobot.com/projects/core/en/stable/user-guide/platform-functionality/data-validation/) rules. They never block a save: results appear under **Extensibility > Data Validation > Data Compliance** and on each object's Data Compliance tab.

| Rule | Checks | Reference |
| --- | --- | --- |
| DNS Delegation Has Name Servers | The delegation has NS records at its owner name. | [RFC 1034 §4.2.1](https://www.rfc-editor.org/rfc/rfc1034.html#section-4.2.1) |
| DNS Delegation In-Domain Glue | Every in-domain name server has an A or AAAA record in the parent zone. | [RFC 9471 §2.1](https://www.rfc-editor.org/rfc/rfc9471.html#section-2.1) |
| DNS Delegation Glue Matches Child Zone | When the child zone exists, its own addresses for each in-domain name server match the glue. | [RFC 9471](https://www.rfc-editor.org/rfc/rfc9471.html) |
| DNS Delegation Name Servers Match Child Zone | When the child zone exists, its apex NS records (`name` `@`) name the same servers as the delegation. | [RFC 1034 §4.2.2](https://www.rfc-editor.org/rfc/rfc1034.html#section-4.2.2) |
| DNS Zone Delegated From Parent | A zone with a parent zone is delegated from it: the parent has NS records, or a DNS delegation, at the zone's name. | [RFC 1034 §4.2.1](https://www.rfc-editor.org/rfc/rfc1034.html#section-4.2.1) |
| *Type* Record Not Below a Zone Cut | A record is not at or below a delegation in its zone. NS records at the cut and A/AAAA records at a delegation's name server names (glue) are exempt. One rule exists per record type. | [RFC 1034 §4.2.1](https://www.rfc-editor.org/rfc/rfc1034.html#section-4.2.1) |

These rules compare several objects, and a result is recorded when the checked object is saved. A result can therefore go stale when a related object changes, for example when glue is added after its delegation was saved. Run the job **Run Registered Data Compliance Rules** to refresh every result.

!!! note
    After upgrading, existing zones that sit below another zone in the same DNS view are reported by "DNS Zone Delegated From Parent" unless the parent zone already has NS records at their name. For example, `test.acme.com` needs an NS record named `test` in `acme.com`.
