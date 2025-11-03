# v1.3 Release Notes

This document describes all new features and changes in the release. The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/) and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## Release Overview

- This release adds the DNS View model. That allows us to model DNS Views, and assign IP prefixes to them, that way we can have DNS Zones served from different Views.
- Changes to compatibility with Nautobot and/or other apps, libraries etc.

<!-- towncrier release notes start -->

## [v1.3.0 (2025-10-29)](https://github.com/nautobot/nautobot-app-dns-models/releases/tag/v1.3.0)

### Added

- [#67](https://github.com/nautobot/nautobot-app-dns-models/issues/67) - Added DNS View model.

### Removed

- [#131](https://github.com/nautobot/nautobot-app-dns-models/issues/131) - Removed duplicate pull request template.
- [#144](https://github.com/nautobot/nautobot-app-dns-models/issues/144) - Removed duplicate searchable_models entry.

### Fixed

- [#119](https://github.com/nautobot/nautobot-app-dns-models/issues/119) - Fixed TTL column not sorting in all views
- [#120](https://github.com/nautobot/nautobot-app-dns-models/issues/120) - Fixed TTL field missing from Record detail views
- [#130](https://github.com/nautobot/nautobot-app-dns-models/issues/130) - Fixed SRVRecord GraphQL type so `srv_record` and `srv_records` are available.
- [#135](https://github.com/nautobot/nautobot-app-dns-models/issues/135) - Fixed ARecord/AAAARecord validation to enforce correct IP version and reject mismatched addresses via ORM writes.
- [#139](https://github.com/nautobot/nautobot-app-dns-models/issues/139) - Fixed missing test coverage for IP Address side panels.

### Housekeeping

- Rebaked from the cookie `nautobot-app-v2.6.0`.
- Rebaked from the cookie `nautobot-app-v2.7.0`.
