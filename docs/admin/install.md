# Installing the App in Nautobot

Here you will find detailed instructions on how to **install** and **configure** the App within your Nautobot environment.

## Prerequisites

- The app is compatible with Nautobot 2.4.4 and higher.
- Databases supported: PostgreSQL, MySQL

!!! note
    Please check the [dedicated page](compatibility_matrix.md) for a full compatibility matrix and the deprecation policy.

### Access Requirements

No access to other systems is required to use this app.

## Install Guide

!!! note
    Apps can be installed from the [Python Package Index](https://pypi.org/) or locally. See the [Nautobot documentation](https://docs.nautobot.com/projects/core/en/stable/user-guide/administration/installation/app-install/) for more details. The pip package name for this app is [`nautobot-dns-models`](https://pypi.org/project/nautobot-dns-models/).

The app is available as a Python package via PyPI and can be installed with `pip`:

```shell
pip install nautobot-dns-models
```

To ensure Nautobot DNS Models is automatically re-installed during future upgrades, create a file named `local_requirements.txt` (if not already existing) in the Nautobot root directory (alongside `requirements.txt`) and list the `nautobot-dns-models` package:

```shell
echo nautobot-dns-models >> local_requirements.txt
```

Once installed, the app needs to be enabled in your Nautobot configuration. The following block of code below shows the additional configuration required to be added to your `nautobot_config.py` file:

- Append `"nautobot_dns_models"` to the `PLUGINS` list.
- Append the `"nautobot_dns_models"` dictionary to the `PLUGINS_CONFIG` dictionary and override any defaults.

```python
# In your nautobot_config.py
PLUGINS = ["nautobot_dns_models"]

# PLUGINS_CONFIG = {
#   "nautobot_dns_models": {
#     ADD YOUR SETTINGS HERE
#   }
# }
```

Once the Nautobot configuration is updated, run the Post Upgrade command (`nautobot-server post_upgrade`) to run migrations and clear any cache:

```shell
nautobot-server post_upgrade
```

Then restart (if necessary) the Nautobot services which may include:

- Nautobot
- Nautobot Workers
- Nautobot Scheduler

```shell
sudo systemctl restart nautobot nautobot-worker nautobot-scheduler
```

## App Configuration

This option is configured via the Admin GUI.

`DNS_VALIDATION_LEVEL` (default: "Wire format")

This setting controls the DNS validation level applied to zones and records:

- **Disabled** - No DNS validation is performed
- **Wire format** - Enforces DNS label and name length rules as specified in [RFC 1035 §3.1](https://datatracker.ietf.org/doc/html/rfc1035#section-3.1):
    - Each label (the parts of the name separated by dots) must be no more than 63 bytes in wire format
    - Empty labels (e.g., consecutive dots or leading/trailing dots) are not allowed
    - The total length of the fully qualified DNS name (including all dots, in wire format) must not exceed 255 bytes