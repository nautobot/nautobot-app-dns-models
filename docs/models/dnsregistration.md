# DNS Registration Model

The DNS registration model tracks registrar-zone assignments and registration lifecycle attributes. A catalog zone is not a registered name, so it cannot be used as `dns_zone`.

- `dns_registrar` (DNS Registrar, mandatory): Registrar used.
- `dns_zone` (DNS Zone, mandatory): Zone that is registered. Must not have a `type` of `Catalog`.
- `status` (Status, mandatory): Registration status.
- `expiration_date` (date, optional): Domain expiration date.
- `auto_renewal` (boolean): Whether auto renewal is enabled.
- `registry_locked` (boolean): Whether registry lock is enabled.
- `transfer_locked` (boolean): Whether transfer lock is enabled.
- `privacy_enabled` (boolean): Whether privacy protection is enabled.
- `website_forwarding_enabled` (boolean): Whether website forwarding is enabled.
- `renewal_term_months` (integer, optional): Renewal term in months.
- `dnssec_enabled` (boolean): Whether DNSSEC is enabled.

Uniqueness is enforced for registrar and zone together, and each zone can only have one registration.
