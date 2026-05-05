# DNS View Model

The DNS View model represents a logical grouping of DNS Zones. A View can be associated with one or more IP Prefixes via DNS View Prefix Assignment, allowing zones and records to be scoped to specific portions of the network.

- `name` (string): Name of the View. Must be unique.
- `description` (string): Description of the View.
- `prefixes` (Prefix, many-to-many): IP Prefixes that define the View. Managed through the `DNSViewPrefixAssignment` model.

A `Default` view is created automatically and is used as the default for new DNS Zones when no view is specified.
