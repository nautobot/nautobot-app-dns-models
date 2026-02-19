# DNS Registrar Model

The DNS registrar model tracks registrar account metadata used by domain zones.

- `name` (string): Unique name of the registrar.
- `url` (string, optional): Registrar portal URL.
- `account_number` (string, optional): Registrar account identifier for your organization.

Registrar-to-zone assignments and registration metadata are tracked through the `DNSRegistration` model.
