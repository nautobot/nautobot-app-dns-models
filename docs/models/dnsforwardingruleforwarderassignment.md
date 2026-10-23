# DNS Forwarding Rule Forwarder Assignment Model

The DNS Forwarding Rule Forwarder Assignment is the through model linking a [DNS forwarding rule](dnsforwardingrule.md) to a [DNS forwarder](dnsforwarder.md). Each `(forwarding_rule, forwarder)` pair is unique.

- `forwarding_rule` (DNSForwardingRule): The forwarding rule.
- `forwarder` (DNSForwarder): A forwarder that resolves the rule's queries.

Assignments are created and deleted through the REST API at `/api/plugins/dns/dns-forwarding-rule-forwarder-assignments/`, and each change is recorded in the change log.
