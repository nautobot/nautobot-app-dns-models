# DNS Forwarding Rule Model

A DNS forwarding rule states that, within a [DNS view](dnsview.md), queries for a domain and the names below it are resolved by sending them to one or more [DNS forwarders](dnsforwarder.md). Forwarding is resolver behavior rather than zone data, so it is modeled separately from [DNS zones](dnszone.md).

- `name` (string): The domain whose queries are forwarded, e.g. `corp.example.com`. Use `.` to forward all queries.
- `dns_view` (DNSView): The DNS view the rule belongs to. Defaults to the `Default` view.
- `forwarders` (list of DNSForwarder): The forwarders that resolve the queries. Read-only in the REST API; see [Assigning forwarders](#assigning-forwarders).
- `description` (string): Description of the rule.

Each `(name, dns_view)` pair is unique. When DNS validation is enabled (via the `DNS_VALIDATION_LEVEL` configuration), each label of `name` must be 1 to 63 bytes in wire format ([RFC 1035 §3.1](https://www.rfc-editor.org/rfc/rfc1035.html#section-3.1)).

The DNS view detail page lists its forwarding rules, and each forwarder's detail page lists the rules that use it.

!!! note
    Behavior that differs between DNS server implementations is not modeled, such as the order in which forwarders are tried, whether a server falls back to its own resolution when forwarders fail, or the transport used to reach them.

## Assigning forwarders

Assignments of forwarders to rules are stored as [DNS Forwarding Rule Forwarder Assignments](dnsforwardingruleforwarderassignment.md).

- **UI:** choose forwarders on the rule's edit form. The bulk edit form can add or remove forwarders on many rules at once.
- **REST API:** create or delete assignments through `/api/plugins/dns/dns-forwarding-rule-forwarder-assignments/`. The `forwarders` field of `/api/plugins/dns/dns-forwarding-rules/` is read-only: a value sent there is ignored.
