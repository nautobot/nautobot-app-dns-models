# CNAME Record Model

+++ 1.2.0 "CNAME exclusivity"

When CNAME exclusivity is enabled (via the `CNAME_RESTRICTION_ENABLED` configuration), the app enforces CNAME rules per [RFC 1912 §2.4](https://datatracker.ietf.org/doc/html/rfc1912#section-2.4):

- A CNAME cannot co‑exist with any other record type that has the exact same `name` in the same `zone`.
- Conversely, a non‑CNAME record cannot co‑exist where a CNAME with the exact same `name` already exists in the same `zone`.
- Name comparison is exact:
    - A zone‑qualified `name` such as `host.example.com` is distinct from the relative `host` under zone `example.com`.
    - A trailing dot is ignored (e.g., `host.example.com.` is treated as `host.example.com`).

Additional constraints:

- Database uniqueness for CNAME is (`name`, `alias`, `zone`).

Examples:

- Blocked: `A(name="www")` and `CNAME(name="www")` in the same zone.
- Allowed: `A(name="www")` and `CNAME(name="www.example.com")` in zone `example.com`.
- Allowed: `A(name="www")` and `CNAME(name="www.example.com.")` (trailing dot ignored).

See the [installation guide](../admin/install.md#app-configuration) for configuration options.