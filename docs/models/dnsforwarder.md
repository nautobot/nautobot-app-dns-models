# DNS Forwarder Model

A DNS forwarder is a name server that resolves queries sent to it by another name server, instead of that server following the authoritative chain itself ([RFC 9499 §6](https://www.rfc-editor.org/rfc/rfc9499.html#section-6)). Forwarders are referenced by [DNS forwarding rules](dnsforwardingrule.md), and one forwarder can serve many rules.

- `name` (string): Unique name of the forwarder, e.g. `Corporate resolver`.
- `ip_address` (IPAddress, optional): The forwarder's address as an IPAM IP Address.
- `address` (string, optional): The forwarder's address as a literal IPv4 or IPv6 address, for resolvers that are not tracked in IPAM, such as public resolvers.
- `port` (integer, default `53`): The port the forwarder listens on, from 1 to 65535.
- `description` (string): Description of the forwarder.

Exactly one of `ip_address` and `address` must be set; an empty `address` counts as not set. Only `name` must be unique: several forwarders may use the same address and port, for example the same private IP in two IPAM namespaces.

An IP Address that a forwarder uses cannot be deleted until the forwarder is changed or deleted. The IP Address detail page lists the forwarders that use it.
