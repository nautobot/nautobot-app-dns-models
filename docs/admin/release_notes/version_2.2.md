# v2.2 Release Notes

This document describes all new features and changes in the release. The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/) and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## Release Overview

- Added functionality to auto-create PTR records in reverse zones when A/AAAA records are created.
- Moved the DNS menu as a top-level option.
- Added global search functionality using FQDN for A/AAAA records.

<!-- towncrier release notes start -->

## [v2.2.0 (2026-07-03)](https://github.com/nautobot/nautobot-app-dns-models/releases/tag/v2.2.0)

### Added

- [#160](https://github.com/nautobot/nautobot-app-dns-models/issues/160) - Added functionality to auto-create PTR records in reverse zone when an A or AAAA record is created in the zone.
- [#228](https://github.com/nautobot/nautobot-app-dns-models/issues/228) - Added functionality to global search using FQDN.

### Changed

- [#182](https://github.com/nautobot/nautobot-app-dns-models/issues/182) - Move DNS menu option to top-level instead of under apps.
- [#216](https://github.com/nautobot/nautobot-app-dns-models/issues/216) - Re-sync invoke lint tasks with cookiecutter by adding `pylint` `target`/`recursive` options and `ruff` `--diff` support.
- [#221](https://github.com/nautobot/nautobot-app-dns-models/issues/221) - Added DNS view in the DNS zone's reference `__str__`.

### Dependencies

- [#230](https://github.com/nautobot/nautobot-app-dns-models/issues/230) - Updated dependencies to latest versions.

### Documentation

- [#207](https://github.com/nautobot/nautobot-app-dns-models/issues/207) - Filled in empty documentation pages for different models.
