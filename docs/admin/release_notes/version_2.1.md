# v2.1 Release Notes

This document describes all new features and changes in the release. The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/) and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## Release Overview

- Major features or milestones
- Changes to compatibility with Nautobot and/or other apps, libraries etc.

<!-- towncrier release notes start -->

## [v2.1.0 (2026-03-18)](https://github.com/nautobot/nautobot-app-dns-models/releases/tag/v2.1.0)

### Added

- [#162](https://github.com/nautobot/nautobot-app-dns-models/issues/162) - Added the `nautobot_dns_models_dns_views` filter extension to the `ipam.Prefix` model to allow filtering prefixes by DNS views.
- [#183](https://github.com/nautobot/nautobot-app-dns-models/issues/183) - Added DNS Registrar tracking

### Changed

- [#123](https://github.com/nautobot/nautobot-app-dns-models/issues/123) - Enforce exact-match CNAME exclusivity (RFC 1912 §2.4) with opt-out `CNAME_RESTRICTION_ENABLED`; normalize trailing-dot names and allow apex; add API/model tests and docs.
- [#181](https://github.com/nautobot/nautobot-app-dns-models/issues/181) - Changed DNSView, ARecord and AAAARecord forms to use DynamicModelChoiceField when applied.

### Fixed

- [#161](https://github.com/nautobot/nautobot-app-dns-models/issues/161) - Fixed AAAA records creation link in DNS zones item object view.
- [#162](https://github.com/nautobot/nautobot-app-dns-models/issues/162) - Fixed the filter for the badge link on the Assigned Prefixes panel in the DNS View detail view.
- [#171](https://github.com/nautobot/nautobot-app-dns-models/issues/171) - Fixed accessing django settings at runtime preventing the Python package from loading.
- [#178](https://github.com/nautobot/nautobot-app-dns-models/issues/178) - Fixed missing preference field from MXRecord table.
- [#179](https://github.com/nautobot/nautobot-app-dns-models/issues/179) - Updated migration to be compatible with Django 5.
- [#188](https://github.com/nautobot/nautobot-app-dns-models/issues/188) - Fixed filters for the DNS Records to include Zone.
- [#192](https://github.com/nautobot/nautobot-app-dns-models/issues/192) - Fixed DNS registration model to use proper Status field.

### Documentation

- [#173](https://github.com/nautobot/nautobot-app-dns-models/issues/173) - Updated documentation to include 3.0 screenshots.

### Housekeeping

- [#194](https://github.com/nautobot/nautobot-app-dns-models/issues/194) - Update Dependencies to prepare for release.
- Rebaked from the cookie `nautobot-app-v3.0.0`.
- Rebaked from the cookie `nautobot-app-v3.1.2`.
