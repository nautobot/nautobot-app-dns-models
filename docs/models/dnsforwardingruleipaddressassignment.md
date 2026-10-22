# DNS Forwarding Rule IP Address Assignment Model

The DNS Forwarding Rule IP Address Assignment is the through model linking a [DNS Forwarding Rule](dnsforwardingrule.md) to an IPAM IP Address, the forwarder. Each `(forwarding_rule, ip_address, port)` combination is unique, so the same server can be listed on two ports.

- `forwarding_rule` (DNSForwardingRule): The rule.
- `ip_address` (IPAddress): The IP address queries are forwarded to.
- `port` (integer, default `53`): The port the forwarder listens on, from 1 to 65535.
- `weight` (integer, default `100`): Forwarders are listed from the lowest to the highest weight. Servers that query forwarders in list order, such as Microsoft DNS, use this order.

A rule with the action `do_not_forward` cannot have forwarders.

In the web UI, forwarders are added, changed, and removed in the **Forwarders** section of the DNS Forwarding Rule create and edit form. The REST API manages them at `/api/plugins/dns/dns-forwarding-rule-ip-address-assignments/`.
