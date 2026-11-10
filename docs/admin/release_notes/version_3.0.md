# v3.0 Release Notes

This document describes all new features and changes in the release. The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/) and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## Release Overview

- Major features or milestones
- Changes to compatibility with Nautobot and/or other apps, libraries etc.

<!-- towncrier release notes start -->

## [v3.0.0 (2026-11-10)](https://github.com/nautobot/nautobot-app-dns-models/releases/tag/v3.0.0)

### Breaking Changes

- [#252](https://github.com/nautobot/nautobot-app-dns-models/issues/252) - Changed DNS Zone name uniqueness within a DNS View to ignore letter case.
- [#252](https://github.com/nautobot/nautobot-app-dns-models/issues/252) - Changed the upgrade migration to abort while DNS Zones in the same DNS View have names that differ only by letter case; see the upgrade guide.
- [#285](https://github.com/nautobot/nautobot-app-dns-models/issues/285) - Changed DNSRegistrar url field name to portal_url.

### Added

- [#252](https://github.com/nautobot/nautobot-app-dns-models/issues/252) - Added the `check_dns_zone_name_collisions` management command to report DNS Zones whose names differ only by letter case.

### Removed

- [#295](https://github.com/nautobot/nautobot-app-dns-models/issues/295) - Dropped support for Python 3.10.

### Fixed

- [#247](https://github.com/nautobot/nautobot-app-dns-models/issues/247) - Fixed creating a DNS Zone through the API without specifying a DNS View (defaults to Default view).
- [#259](https://github.com/nautobot/nautobot-app-dns-models/issues/259) - Fixed the `Auto-create PTR Records` column in the DNS Zone table to render the same check/X icons as the detail view and the other boolean columns, instead of plain Unicode characters.
- [#265](https://github.com/nautobot/nautobot-app-dns-models/issues/265) - Fixed the SOA Retry field label in the DNS Zone bulk edit form.
- [#266](https://github.com/nautobot/nautobot-app-dns-models/issues/266) - Fixed DNS Zone bulk edit rejecting valid SOA RNAME values.
- [#271](https://github.com/nautobot/nautobot-app-dns-models/issues/271) - Fixed the IP Address field label on the A Record and AAAA Record forms displaying as "Ip address".
- [#273](https://github.com/nautobot/nautobot-app-dns-models/issues/273) - Fixed `TXTRecord.text` being limited to 256 characters, which rejected valid records such as 2048-bit DKIM keys. TXT content now follows RFC 1035 §3.3.14: up to 65535 bytes in total, split into `<character-string>` values of up to 255 bytes each. Long values are split automatically, and explicit DNS presentation format (`"part one" "part two"`) is accepted to control where the boundaries fall.

### Housekeeping

- [#268](https://github.com/nautobot/nautobot-app-dns-models/issues/268) - Fixed fourteen filter tests that asserted their own fixture's row count instead of exercising the named filter.
- [#273](https://github.com/nautobot/nautobot-app-dns-models/issues/273) - Moved TXT record content validation from a Data Validation Engine compliance rule into `TXTRecord.clean()`.
- [#300](https://github.com/nautobot/nautobot-app-dns-models/issues/300) - Merged unreleased migrations into a single one.
