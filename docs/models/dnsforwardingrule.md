# DNS Forwarding Rule Model

A DNS Forwarding Rule tells the resolvers of a DNS View what to do with queries for a domain: send them to specific servers (forwarders), or exempt the domain from a broader rule. One vendor-agnostic model covers conditional forwarders, global forwarders, and cloud resolver rules.

- `name` (string): The domain the rule applies to, for example `corp.example.com`. A single dot (`.`) holds the global forwarders, which apply to every name that no more specific rule or zone covers.
- `dns_view` (DNSView): The DNS View the rule applies in. Defaults to the `Default` view.
- `action` (choice, default `forward_first`): What the resolvers do with matching queries.
    - `forward_first` (Forward first): Send queries to the forwarders, and fall back to normal resolution if they do not answer.
    - `forward_only` (Forward only): Send queries to the forwarders only. If they do not answer, the query fails.
    - `do_not_forward` (Do not forward): Resolve normally. Use it to exempt a subdomain from a broader rule, for example `public.partner.example.net` under a rule for `partner.example.net`. Such a rule cannot have forwarders.
- `forwarders` (IP Addresses, read-only): The IP addresses queries are forwarded to. They are managed as [DNS Forwarding Rule IP Address Assignments](dnsforwardingruleipaddressassignment.md), which also hold each forwarder's port and weight.
- `enabled` (boolean, default `True`): Indicates whether the rule is eligible for publication by external integrations. This app does not publish rules or enforce this setting.
- `description` (string): Description of the rule.
- `tenant` (Tenant, optional): Reference to the Tenant model for multi-tenancy support.

Forwarders are IPAM IP Address objects, like the addresses of A and AAAA records. A forwarder outside your network, such as a public resolver or a partner's DNS server, therefore needs an IP Address in Nautobot, which in turn needs a parent Prefix in its Namespace.

## Validation

- The name is unique within a DNS View.
- The name cannot match a [DNS Zone](dnszone.md) in the same DNS View, because a rule cannot replace an authoritative zone.
- A `do_not_forward` rule cannot have forwarders. To change a rule with forwarders to `do_not_forward`, remove its forwarders first.
- When the `DNS_VALIDATION_LEVEL` setting is `wire-format`, each label of the name must be non-empty and at most 63 bytes in wire format, as for zones.

## Rule Checks

The rule detail page shows a **Rule Checks** panel when the rule cannot work as intended:

- A `forward_first` or `forward_only` rule has no forwarders.
- The rule's domain is inside a zone in the same DNS View, and that zone has no delegation (NS records) at or above the domain. BIND and Microsoft DNS answer names inside a zone they host from the zone itself, so the rule only takes effect once the domain is delegated. See [Delegation](dnszone.md#delegation).

These are warnings only and never block saving.

## Mapping to DNS Platforms

This app does not configure DNS servers. The table shows how the model corresponds to common platforms, for anyone exporting the data or building an integration.

| Platform | Rule | Forwarders | Action | DNS View |
| --- | --- | --- | --- | --- |
| BIND | `zone "corp.example.com" { type forward; ... };`. Global forwarders go in `options`. | `forwarders { 10.0.0.53 port 53; };` | `forward first;` or `forward only;`. Do not forward is an empty `forwarders { };`. | `view` statement |
| Microsoft DNS | Conditional forwarder. Global forwarders are the server's forwarders. | Master servers, queried in list order | Forward first and Forward only correspond to whether recursion is used after the forwarders fail (`UseRecursion`, or "Use root hints if no forwarders are available" for global forwarders). | DNS server or AD replication scope |
| Infoblox NIOS | Forward zone | `forward_to` servers | Forward only corresponds to "forwarders only". | DNS View |
| Unbound | `forward-zone` | `forward-addr: 10.0.0.53@53` | `forward-first: yes` or `no` | Not applicable |
| AWS Route 53 Resolver | Resolver rule | Target IP addresses and ports | FORWARD rules are Forward only. SYSTEM rules are Do not forward. | VPC associations |
| Azure DNS Private Resolver | Rule in a DNS forwarding ruleset | Destination IP addresses and ports | Forward only | Virtual network links of the ruleset |

The forwarders' `weight` sets the order in which they are listed. Servers that query forwarders in list order, such as Microsoft DNS, use that order. BIND and Unbound choose forwarders by response time instead.
