
# v1.2 Release Notes

This document describes all new features and changes in the release. The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/) and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## Release Overview

This release makes DNS models globally searchable in Nautobot and added DNS name length validation per RFC 1035.

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
