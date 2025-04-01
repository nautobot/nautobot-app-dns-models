# v0.2 Release Notes

This document describes all new features and changes in the release. The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/) and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## Release Overview

## [v0.2.1 (2025-04-01)](https://github.com/nautobot/nautobot-app-dns-models/releases/tag/v0.2.1)

### Changed

- [#59](https://github.com/nautobot/nautobot-app-dns-models/issues/59) - Make navigation DNS title standard.

### Fixed

- [#52](https://github.com/nautobot/nautobot-app-dns-models/issues/52) - Fixed a couple of unittests.
- [#52](https://github.com/nautobot/nautobot-app-dns-models/issues/52) - Fixed to use `fields = "__all__"` in forms.

### Housekeeping

- [#58](https://github.com/nautobot/nautobot-app-dns-models/issues/58) - Changed to correct token for release job.
- [#58](https://github.com/nautobot/nautobot-app-dns-models/issues/58) - Removed jquery loading for RTD flyout.
- [#62](https://github.com/nautobot/nautobot-app-dns-models/issues/62) - Set minimum python version to 3.9.2 in line with Nautobot Core. This is necessary due to upstream `cryptography` constraints, see [#7019](https://github.com/nautobot/nautobot/pull/7019).

## [v0.2.0 (2025-03-26)](https://github.com/nautobot/nautobot-app-dns-models/releases/tag/v0.2.0)

Initial app release.
