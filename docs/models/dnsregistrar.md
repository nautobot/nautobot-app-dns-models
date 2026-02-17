# DNS Registrar Model

The DNS registrar model tracks registrar account metadata used by domain zones.

- `name` (string): Unique name of the registrar.
- `url` (string, optional): Registrar portal URL.
- `account_number` (string, optional): Registrar account identifier for your organization.

DNS zones can optionally reference a registrar through the `dns_registrar` field.
