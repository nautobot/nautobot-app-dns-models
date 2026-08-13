# v2.3 Release Notes

This document describes all new features and changes in the release. The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/) and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## Release Overview

- Added `enabled` field in DNS Zones and every record type models with `True` as the default.
- Changed fields to comply with RFC using 32-bit range values. 

<!-- towncrier release notes start -->

## [v2.3.0 (2026-08-13)](https://github.com/nautobot/nautobot-app-dns-models/releases/tag/v2.3.0)

### Added

- [#222](https://github.com/nautobot/nautobot-app-dns-models/issues/222) - Added an `enabled` boolean field to `DNSZone` (default `True`) to indicate whether a zone is eligible for publication by external integrations.
- [#256](https://github.com/nautobot/nautobot-app-dns-models/issues/256) - Added the `enabled` boolean field (default `True`) to every DNS record type by moving it from `DNSZone` up to the shared `DNSModel` base class. The zone and record flags are independent: disabling a zone does not disable the records it contains.

### Changed

- [#217](https://github.com/nautobot/nautobot-app-dns-models/issues/217) - Added more fields to the DNS Zone Bulk Edit form.

### Fixed

- [#214](https://github.com/nautobot/nautobot-app-dns-models/issues/214) - Fixed DNS integer fields (Zone TTL, SOA refresh/retry/expire/serial/minimum, record TTL) to support the full RFC-compliant unsigned 32-bit range (0–4294967295).
- [#214](https://github.com/nautobot/nautobot-app-dns-models/issues/214) - Fixed a bug where a record TTL of 0 was treated as unset and silently replaced by the zone TTL.
- [#224](https://github.com/nautobot/nautobot-app-dns-models/issues/224) - Changed `DNSZone.soa_rname` to accept single-label placeholders and normalize supported DNS-style mailboxes to email form.
- [#243](https://github.com/nautobot/nautobot-app-dns-models/issues/243) - Fixed auto-create PTR records field to look the same as the other boolean fields in buld edit form.

### Housekeeping

- [#233](https://github.com/nautobot/nautobot-app-dns-models/issues/233) - 
- [#258](https://github.com/nautobot/nautobot-app-dns-models/issues/258) - Cleaned up migrations prior to new release.
- [#261](https://github.com/nautobot/nautobot-app-dns-models/issues/261) - Update dependencies and prepare for 2.3.0 release.
- Rebaked from the cookie `nautobot-app-v3.1.4`.
