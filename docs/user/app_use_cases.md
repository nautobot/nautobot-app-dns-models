# Using the App

This document describes common use-cases and scenarios for this App.

## General Usage

Generally, this App is to used to keep track of DNS Zones and their related data and records. The idea is to have a set of models that can either be used to directly model DNS configurations or as a place to aggregate data about DNS related configuration from other tools. While A, AAAA, and PTR records are already partially supported within Nautobot core models, this App is meant to expand the type of DNS records and formalize DNS models within Nautobot.

## Use-cases and common workflows

Use the API or GUI to add DNS Zones and Record objects to Nautobot.

### Modeling a Zone Delegation

Delegate a subdomain to other name servers, either to a zone you also model in Nautobot or to one run elsewhere:

1. Optionally create the child zone, for example `apps.example.com`, in the same DNS View as the parent. Nautobot sets its **Parent Zone** to `example.com` automatically.
2. In the parent zone, add one NS record per name server of the child, named after the delegated label, for example `apps` with server `ns1.apps.example.com`.
3. If a name server sits inside the delegated name, add its glue record in the parent zone, for example an A record `ns1.apps`.
4. Open the parent zone. The **Delegations** panel lists the delegation, its glue, and its child zone or "External". The **Delegation Checks** panel reports anything inconsistent, such as missing glue or NS records that differ from the child zone's own.

There is no separate delegation object: the NS and glue records are the delegation. See [Delegation](../models/dnszone.md#delegation) for the details and every check.

### Modeling Forwarding Rules

Record how the resolvers of a DNS View forward queries:

1. Make sure each forwarder exists as an IP Address in Nautobot. External resolvers, such as a partner's DNS servers, need an IP Address and a parent Prefix like any other address.
2. Create a DNS Forwarding Rule with the domain, the DNS View, and the action. Use `.` as the domain for the global forwarders.
3. In the **Forwarders** section of the same form, add each forwarder's IP address, port, and weight. Lower weights are listed first.
4. To exempt a subdomain from a broader rule, create a rule for the subdomain with the action **Do not forward** and no forwarders.

A rule for a name inside a zone that the same view hosts only works if the zone delegates that name. The rule's **Rule Checks** panel warns about this and about rules without forwarders. See [DNS Forwarding Rule](../models/dnsforwardingrule.md) for how the model maps to BIND, Microsoft DNS, Infoblox, Unbound, and cloud resolvers.

## Screenshots

![Adding a DNS Zone](../images/getting_started-add-zone-3-light.png#only-light){ .on-glb }
![Adding a DNS Zone](../images/getting_started-add-zone-3-dark.png#only-dark){ .on-glb }
[//]: # "`https://next.demo.nautobot.com/plugins/dns/dns-zones/add/`"

/// caption
Adding a DNS Zone
///

![DNS Zone View](../images/getting_started-add-record-3-light.png#only-light){ .on-glb }
![DNS Zone View](../images/getting_started-add-record-3-dark.png#only-dark){ .on-glb }
/// caption
The DNS Zone View
///
