
# v1.2 Release Notes

This document describes all new features and changes in the release. The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/) and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## Release Overview

- This release makes DNS models globally searchable in Nautobot and added DNS name length validation per RFC 1035.
- Changes to compatibility with Nautobot and/or other apps, libraries etc.

## [v1.2.2 (2025-09-26)](https://github.com/nautobot/nautobot-app-dns-models/releases/tag/v1.2.2)

### Added

- [#113](https://github.com/nautobot/nautobot-app-dns-models/issues/113) - Add q SearchFilter to DNSZoneFilterSet to enable API q= search.
- [#122](https://github.com/nautobot/nautobot-app-dns-models/issues/122) - Added q SearchFilter for models to enable global search.

## [v1.2.1 (2025-09-16)](https://github.com/nautobot/nautobot-app-dns-models/releases/tag/v1.2.1)

### Fixed

- [#100](https://github.com/nautobot/nautobot-app-dns-models/issues/100) - Fixed TTL field missing from GraphQL DNS record's schemas.

### Dependencies

- [#108](https://github.com/nautobot/nautobot-app-dns-models/issues/108) - Pinned Django debug toolbar to <6.0.0.

### Housekeeping

- [#90](https://github.com/nautobot/nautobot-app-dns-models/issues/90) - Housekeeping removed `Model` suffix from models.
- Rebaked from the cookie `nautobot-app-v2.5.1`.

## [v1.2.0 (2025-07-25)](https://github.com/nautobot/nautobot-app-dns-models/releases/tag/v1.2.0)

### Added

- [#93](https://github.com/nautobot/nautobot-app-dns-models/issues/93) - Added searchable models to the app config to make DNS models globally searchable.

### Changed

- [#87](https://github.com/nautobot/nautobot-app-dns-models/issues/87) - Changed TTL of DNS Records to be optional and inherited from the zone if no value is provided.

### Fixed

- [#45](https://github.com/nautobot/nautobot-app-dns-models/issues/45) - Fixed issue where ARecord model would accept IPv6 addresses.
- [#45](https://github.com/nautobot/nautobot-app-dns-models/issues/45) - Fixed issue where AAAARecords model would accept IPv4 addresses.
- [#76](https://github.com/nautobot/nautobot-app-dns-models/issues/76) - Added DNS name length validation per RFC 1035 §3.1 for zone and record names.
- [#98](https://github.com/nautobot/nautobot-app-dns-models/issues/98) - Fixed conflicting migrations.
- [#102](https://github.com/nautobot/nautobot-app-dns-models/issues/102) - Fixed unittest for PTRRecordModelViewTest.
